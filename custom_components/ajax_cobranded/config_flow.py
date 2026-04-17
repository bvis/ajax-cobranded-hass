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
    CONF_PHOTO_MAX_PER_DEVICE,
    CONF_PHOTO_RETENTION_DAYS,
    DEFAULT_PHOTO_MAX_PER_DEVICE,
    DEFAULT_PHOTO_RETENTION_DAYS,
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
            _LOGGER.debug("Config flow: app_label=%s", self._app_label)
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
            except Exception as e:
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
                assert self._client is not None
                await asyncio.wait_for(
                    self._client.login_totp(
                        email=self._email,
                        request_id=self._request_id,
                        totp_code=user_input["totp_code"],
                    ),
                    timeout=30,
                )
                return await self.async_step_select_spaces()
            except AuthenticationError:
                errors["base"] = "invalid_totp"
            except TimeoutError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during 2FA")
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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration (change credentials)."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            email = user_input["email"]
            password_hash = AjaxSession.hash_password(user_input["password"])
            app_label = user_input.get("app_label", entry.data.get("app_label", APPLICATION_LABEL))
            try:
                client = AjaxGrpcClient(
                    email=email,
                    password_hash=password_hash,
                    app_label=app_label,
                )
                await client.connect()
                await asyncio.wait_for(client.login(), timeout=30)
                await client.close()
                # Update unique_id if email changed
                if email != entry.unique_id:
                    await self.async_set_unique_id(email)
                    self._abort_if_unique_id_configured(updates={"email": email})
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        **entry.data,
                        "email": email,
                        "password_hash": password_hash,
                        "app_label": app_label,
                    },
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except (ConnectionError, OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reconfigure")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required("email", default=entry.data.get("email", "")): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL)
                    ),
                    vol.Required("password"): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(
                        "app_label",
                        default=entry.data.get("app_label", APPLICATION_LABEL),
                    ): SelectSelector(
                        SelectSelectorConfig(options=KNOWN_APP_LABELS, custom_value=True, sort=True)
                    ),
                }
            ),
            errors=errors,
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
                    vol.Optional(
                        CONF_PHOTO_RETENTION_DAYS,
                        default=self._config_entry.options.get(
                            CONF_PHOTO_RETENTION_DAYS, DEFAULT_PHOTO_RETENTION_DAYS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
                    vol.Optional(
                        CONF_PHOTO_MAX_PER_DEVICE,
                        default=self._config_entry.options.get(
                            CONF_PHOTO_MAX_PER_DEVICE, DEFAULT_PHOTO_MAX_PER_DEVICE
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=10000)),
                }
            ),
        )
