"""Config flow for Ajax Security integration."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.session import (
    AjaxSession,
    AuthenticationError,
    TwoFactorRequiredError,
)
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import (
    APPLICATION_LABEL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    KNOWN_APP_LABELS,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required("email"): TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL)),
        vol.Required("password"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        vol.Optional("app_label", default=APPLICATION_LABEL): SelectSelector(
            SelectSelectorConfig(options=KNOWN_APP_LABELS, custom_value=True, sort=True)
        ),
    }
)

TOTP_SCHEMA = vol.Schema(
    {
        vol.Required("totp_code"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
    }
)


class AjaxCobrandedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ajax Security."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        self._client: AjaxGrpcClient | None = None
        self._email: str = ""
        self._password_hash: str = ""
        self._app_label: str = APPLICATION_LABEL
        self._request_id: str = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input["email"]
            self._password_hash = AjaxSession.hash_password(user_input["password"])
            self._app_label = user_input.get("app_label", APPLICATION_LABEL)
            _LOGGER.debug("Config flow: email=%s, app_label=%s", self._email, self._app_label)
            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()
            try:
                self._client = AjaxGrpcClient(
                    email=self._email,
                    password_hash=self._password_hash,
                    app_label=self._app_label,
                )
                await self._client.connect()
                await asyncio.wait_for(self._client.login(), timeout=30)
                return await self.async_step_select_spaces()
            except TwoFactorRequiredError as e:
                self._request_id = e.request_id
                return await self.async_step_2fa()
            except AuthenticationError as e:
                _LOGGER.error("Authentication failed: %s", e)
                errors["base"] = "invalid_auth"
            except (ConnectionError, OSError) as e:
                _LOGGER.error("Connection failed: %s", e)
                errors["base"] = "cannot_connect"
            except TimeoutError:
                _LOGGER.error("Login timed out")
                errors["base"] = "cannot_connect"
            except asyncio.CancelledError:
                _LOGGER.error("Login was cancelled")
                errors["base"] = "unknown"
            except BaseException as e:
                _LOGGER.error(
                    "Unexpected error during login: %s: %s",
                    type(e).__name__,
                    e,
                    exc_info=True,
                )
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)

    async def async_step_2fa(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self.async_step_select_spaces()
            except AuthenticationError:
                errors["base"] = "invalid_totp"
            except Exception:
                _LOGGER.error("Unexpected error during 2FA")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="2fa", data_schema=TOTP_SCHEMA, errors=errors)

    async def async_step_select_spaces(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            assert self._client is not None
            return self.async_create_entry(
                title=f"Ajax Security ({self._email})",
                data={
                    "email": self._email,
                    "password_hash": self._password_hash,
                    "app_label": self._app_label,
                    "spaces": user_input["spaces"],
                    "device_id": self._client.session.device_id,
                },
            )
        if self._client:
            spaces_api = SpacesApi(self._client)
            spaces = await spaces_api.list_spaces()
            space_options = [SelectOptionDict(value=s.id, label=s.name) for s in spaces]
        else:
            space_options = []
        return self.async_show_form(
            step_id="select_spaces",
            data_schema=vol.Schema(
                {
                    vol.Required("spaces"): SelectSelector(
                        SelectSelectorConfig(
                            options=space_options,
                            multiple=True,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AjaxCobrandedOptionsFlow:
        return AjaxCobrandedOptionsFlow(config_entry)


class AjaxCobrandedOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            if user_input.get("pin_code"):
                user_input["pin_code_hash"] = hashlib.sha256(
                    user_input.pop("pin_code").encode()
                ).hexdigest()
            else:
                user_input.pop("pin_code", None)
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "poll_interval",
                        default=self._config_entry.options.get(
                            "poll_interval", DEFAULT_POLL_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=30, max=300)),
                    vol.Optional(
                        "use_pin_code",
                        default=self._config_entry.options.get("use_pin_code", False),
                    ): bool,
                    vol.Optional("pin_code"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(
                        "fcm_project_id",
                        default=self._config_entry.options.get("fcm_project_id", ""),
                    ): str,
                    vol.Optional(
                        "fcm_app_id",
                        default=self._config_entry.options.get("fcm_app_id", ""),
                    ): str,
                    vol.Optional(
                        "fcm_api_key",
                        default=self._config_entry.options.get("fcm_api_key", ""),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                    vol.Optional(
                        "fcm_sender_id",
                        default=self._config_entry.options.get("fcm_sender_id", ""),
                    ): str,
                }
            ),
        )
