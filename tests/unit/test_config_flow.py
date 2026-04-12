"""Tests for config flow."""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.session import AuthenticationError, TwoFactorRequiredError
from custom_components.ajax_cobranded.config_flow import (
    AjaxCobrandedConfigFlow,
    AjaxCobrandedOptionsFlow,
)
from custom_components.ajax_cobranded.const import DOMAIN


class TestConfigFlowInit:
    def test_domain(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        assert flow.DOMAIN == DOMAIN

    def test_has_user_step(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        assert hasattr(flow, "async_step_user")

    def test_has_2fa_step(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        assert hasattr(flow, "async_step_2fa")

    def test_has_select_spaces_step(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        assert hasattr(flow, "async_step_select_spaces")

    def test_version(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        assert flow.VERSION == 1


class TestAsyncStepUser:
    @pytest.mark.asyncio
    async def test_step_user_no_input_shows_form(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        await flow.async_step_user(None)
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args[1]["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_invalid_auth(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=AuthenticationError("invalid"))

        with patch(
            "custom_components.ajax_cobranded.config_flow.AjaxGrpcClient", return_value=mock_client
        ):
            await flow.async_step_user({"email": "a@b.com", "password": "bad"})

        assert flow.async_show_form.call_args[1]["errors"]["base"] == "invalid_auth"

    @pytest.mark.asyncio
    async def test_step_user_cannot_connect(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=ConnectionError("refused"))

        with patch(
            "custom_components.ajax_cobranded.config_flow.AjaxGrpcClient", return_value=mock_client
        ):
            await flow.async_step_user({"email": "a@b.com", "password": "pass"})

        assert flow.async_show_form.call_args[1]["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_step_user_unknown_error(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=RuntimeError("unexpected"))

        with patch(
            "custom_components.ajax_cobranded.config_flow.AjaxGrpcClient", return_value=mock_client
        ):
            await flow.async_step_user({"email": "a@b.com", "password": "pass"})

        assert flow.async_show_form.call_args[1]["errors"]["base"] == "unknown"

    @pytest.mark.asyncio
    async def test_step_user_2fa_required(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=TwoFactorRequiredError("req-123"))

        with patch(
            "custom_components.ajax_cobranded.config_flow.AjaxGrpcClient", return_value=mock_client
        ):
            await flow.async_step_user({"email": "a@b.com", "password": "pass"})

        # Should have shown 2fa form
        assert flow._request_id == "req-123"

    @pytest.mark.asyncio
    async def test_step_user_stores_password_hash_not_plaintext(self) -> None:
        """Ensure plaintext password is never stored; only the hash is kept."""
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=ConnectionError("refused"))

        with patch(
            "custom_components.ajax_cobranded.config_flow.AjaxGrpcClient", return_value=mock_client
        ):
            await flow.async_step_user({"email": "a@b.com", "password": "mypassword"})

        expected_hash = hashlib.sha256(b"mypassword").hexdigest()
        assert flow._password_hash == expected_hash
        # The flow object should not have _password attribute with plaintext
        assert not hasattr(flow, "_password") or getattr(flow, "_password", None) != "mypassword"


class TestAsyncStep2FA:
    @pytest.mark.asyncio
    async def test_step_2fa_no_input_shows_form(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        await flow.async_step_2fa(None)
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args[1]["step_id"] == "2fa"

    @pytest.mark.asyncio
    async def test_step_2fa_invalid_totp(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_step_select_spaces = AsyncMock(side_effect=AuthenticationError("bad totp"))

        await flow.async_step_2fa({"totp_code": "000000"})
        assert flow.async_show_form.call_args[1]["errors"]["base"] == "invalid_totp"

    @pytest.mark.asyncio
    async def test_step_2fa_unknown_error(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_step_select_spaces = AsyncMock(side_effect=RuntimeError("unknown"))

        await flow.async_step_2fa({"totp_code": "000000"})
        assert flow.async_show_form.call_args[1]["errors"]["base"] == "unknown"


class TestAsyncStepSelectSpaces:
    @pytest.mark.asyncio
    async def test_step_select_spaces_no_client_shows_form(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow._client = None

        await flow.async_step_select_spaces(None)
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_step_select_spaces_with_input_creates_entry(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow._email = "test@example.com"
        flow._password_hash = hashlib.sha256(b"secret").hexdigest()

        mock_client = MagicMock()
        mock_client.session.device_id = "dev-uuid"
        flow._client = mock_client

        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_select_spaces({"spaces": ["space-1"]})
        flow.async_create_entry.assert_called_once()
        call_kwargs = flow.async_create_entry.call_args[1]
        assert call_kwargs["data"]["email"] == "test@example.com"
        assert call_kwargs["data"]["spaces"] == ["space-1"]
        # Ensure password_hash is stored, not plaintext password
        assert "password_hash" in call_kwargs["data"]
        assert "password" not in call_kwargs["data"]
        # Ensure session token is NOT stored
        assert "session_token" not in call_kwargs["data"]
        assert "user_hex_id" not in call_kwargs["data"]

    @pytest.mark.asyncio
    async def test_step_select_spaces_with_client_loads_spaces(self) -> None:
        flow = AjaxCobrandedConfigFlow()
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        mock_space = MagicMock()
        mock_space.id = "space-1"
        mock_space.name = "Home"

        mock_client = MagicMock()
        flow._client = mock_client

        mock_spaces_api = MagicMock()
        mock_spaces_api.list_spaces = AsyncMock(return_value=[mock_space])

        with patch(
            "custom_components.ajax_cobranded.config_flow.SpacesApi", return_value=mock_spaces_api
        ):
            await flow.async_step_select_spaces(None)

        flow.async_show_form.assert_called_once()


class TestOptionsFlow:
    def test_options_flow_init(self) -> None:
        config_entry = MagicMock()
        config_entry.options = {}
        flow = AjaxCobrandedOptionsFlow(config_entry)
        assert flow._config_entry is config_entry

    @pytest.mark.asyncio
    async def test_options_flow_no_input_shows_form(self) -> None:
        config_entry = MagicMock()
        config_entry.options = {"poll_interval": 60, "use_pin_code": False}
        flow = AjaxCobrandedOptionsFlow(config_entry)
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        await flow.async_step_init(None)
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_options_flow_with_input_creates_entry(self) -> None:
        config_entry = MagicMock()
        config_entry.options = {}
        flow = AjaxCobrandedOptionsFlow(config_entry)
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_init({"poll_interval": 60, "use_pin_code": True})
        flow.async_create_entry.assert_called_once_with(
            title="", data={"poll_interval": 60, "use_pin_code": True}
        )

    @pytest.mark.asyncio
    async def test_options_flow_with_pin_code_stores_hash(self) -> None:
        """Ensure the pin code is stored as a hash, not plaintext."""
        config_entry = MagicMock()
        config_entry.options = {}
        flow = AjaxCobrandedOptionsFlow(config_entry)
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_init({"poll_interval": 60, "use_pin_code": True, "pin_code": "1234"})
        flow.async_create_entry.assert_called_once()
        stored_data = flow.async_create_entry.call_args[1]["data"]
        assert "pin_code" not in stored_data
        expected_hash = hashlib.sha256(b"1234").hexdigest()
        assert stored_data["pin_code_hash"] == expected_hash

    @pytest.mark.asyncio
    async def test_options_flow_without_pin_code_no_hash(self) -> None:
        """Ensure no pin_code_hash is stored when pin_code is empty."""
        config_entry = MagicMock()
        config_entry.options = {}
        flow = AjaxCobrandedOptionsFlow(config_entry)
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_init({"poll_interval": 60, "use_pin_code": False})
        stored_data = flow.async_create_entry.call_args[1]["data"]
        assert "pin_code" not in stored_data
        assert "pin_code_hash" not in stored_data
