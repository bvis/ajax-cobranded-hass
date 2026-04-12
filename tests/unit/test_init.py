"""Tests for the integration __init__.py setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAsyncSetupEntry:
    @pytest.mark.asyncio
    async def test_setup_entry_creates_coordinator(self) -> None:
        from custom_components.ajax_cobranded import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "entry-1"
        entry.data = {
            "email": "test@example.com",
            "password_hash": "abc123hash",
            "spaces": ["s1"],
        }
        entry.options = {"poll_interval": 30}

        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.session = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.async_start_push_notifications = AsyncMock()

        with (
            patch(
                "custom_components.ajax_cobranded.AjaxGrpcClient", return_value=mock_client
            ) as mock_cls,
            patch(
                "custom_components.ajax_cobranded.AjaxCobrandedCoordinator",
                return_value=mock_coordinator,
            ),
        ):
            result = await async_setup_entry(hass, entry)

        assert result is True
        assert entry.runtime_data is mock_coordinator
        # Verify client was created with password_hash, not password
        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("password_hash") == "abc123hash"
        assert "password" not in call_kwargs or call_kwargs.get("password") is None

    @pytest.mark.asyncio
    async def test_setup_entry_with_legacy_password(self) -> None:
        """Test backward compatibility: legacy entries with plaintext password still work."""
        from custom_components.ajax_cobranded import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "entry-legacy"
        entry.data = {
            "email": "test@example.com",
            "password": "secret",
            "spaces": ["s1"],
        }
        entry.options = {}

        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.session = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.async_start_push_notifications = AsyncMock()

        with (
            patch(
                "custom_components.ajax_cobranded.AjaxGrpcClient", return_value=mock_client
            ) as mock_cls,
            patch(
                "custom_components.ajax_cobranded.AjaxCobrandedCoordinator",
                return_value=mock_coordinator,
            ),
        ):
            result = await async_setup_entry(hass, entry)

        assert result is True
        # Verify client was created with plaintext password (legacy path)
        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs.get("password") == "secret"

    @pytest.mark.asyncio
    async def test_setup_entry_does_not_restore_session_token(self) -> None:
        """Ensure session token is no longer read from config entry data."""
        from custom_components.ajax_cobranded import async_setup_entry

        hass = MagicMock()
        hass.data = {}
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "entry-2"
        entry.data = {
            "email": "test@example.com",
            "password_hash": "abc123hash",
            "spaces": ["s1"],
        }
        entry.options = {}

        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.session = MagicMock()

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.async_start_push_notifications = AsyncMock()

        with (
            patch("custom_components.ajax_cobranded.AjaxGrpcClient", return_value=mock_client),
            patch(
                "custom_components.ajax_cobranded.AjaxCobrandedCoordinator",
                return_value=mock_coordinator,
            ),
        ):
            result = await async_setup_entry(hass, entry)

        assert result is True
        # Session token should NOT be restored — authentication happens fresh via coordinator
        mock_client.session.set_session.assert_not_called()


class TestAsyncUnloadEntry:
    @pytest.mark.asyncio
    async def test_unload_entry_success(self) -> None:
        from custom_components.ajax_cobranded import async_unload_entry

        mock_coordinator = MagicMock()
        mock_coordinator.async_shutdown = AsyncMock()

        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "entry-1"
        entry.runtime_data = mock_coordinator

        result = await async_unload_entry(hass, entry)

        assert result is True
        mock_coordinator.async_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_unload_entry_failure_does_not_clean_up(self) -> None:
        from custom_components.ajax_cobranded import async_unload_entry

        mock_coordinator = MagicMock()
        mock_coordinator.async_shutdown = AsyncMock()

        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        entry = MagicMock()
        entry.entry_id = "entry-1"
        entry.runtime_data = mock_coordinator

        result = await async_unload_entry(hass, entry)

        assert result is False
        mock_coordinator.async_shutdown.assert_not_called()
