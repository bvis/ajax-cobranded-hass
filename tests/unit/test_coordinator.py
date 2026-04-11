"""Tests for the data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.models import Device, Space
from custom_components.ajax_cobranded.const import ConnectionStatus, DeviceState, SecurityState


def _make_space(space_id: str = "s1") -> Space:
    return Space(
        id=space_id,
        hub_id="hub-1",
        name="Home",
        security_state=SecurityState.DISARMED,
        connection_status=ConnectionStatus.ONLINE,
        malfunctions_count=0,
    )


def _make_device(device_id: str = "d1") -> Device:
    return Device(
        id=device_id,
        hub_id="hub-1",
        name="Sensor",
        device_type="door_protect",
        room_id=None,
        group_id=None,
        state=DeviceState.ONLINE,
        malfunctions=0,
        bypassed=False,
        statuses={},
        battery=None,
    )


def _make_coordinator(
    space_ids: list[str] | None = None,
) -> AjaxCobrandedCoordinator:  # noqa: F821
    """Create coordinator with DataUpdateCoordinator.__init__ patched."""
    from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

    hass = MagicMock()
    client = MagicMock()
    with patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coordinator = AjaxCobrandedCoordinator(
            hass=hass, client=client, space_ids=space_ids or ["s1"], poll_interval=30
        )
    return coordinator


class TestCoordinatorInit:
    def test_attributes(self) -> None:
        coordinator = _make_coordinator()
        assert coordinator._space_ids == ["s1"]

    def test_data_structure(self) -> None:
        coordinator = _make_coordinator()
        assert coordinator.spaces == {}
        assert coordinator.devices == {}

    def test_security_api_property(self) -> None:
        coordinator = _make_coordinator()
        assert coordinator.security_api is coordinator._security_api

    def test_devices_api_property(self) -> None:
        coordinator = _make_coordinator()
        assert coordinator.devices_api is coordinator._devices_api


class TestAsyncUpdateData:
    @pytest.mark.asyncio
    async def test_update_data_when_authenticated(self) -> None:
        coordinator = _make_coordinator()
        coordinator._client.session.is_authenticated = True

        space = _make_space("s1")
        device = _make_device("d1")

        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(return_value=[space])
        coordinator._devices_api = MagicMock()
        coordinator._devices_api.get_devices_snapshot = AsyncMock(return_value=[device])

        result = await coordinator._async_update_data()
        assert "spaces" in result
        assert "devices" in result
        assert "s1" in result["spaces"]
        assert "d1" in result["devices"]

    @pytest.mark.asyncio
    async def test_update_data_logs_in_when_not_authenticated(self) -> None:
        coordinator = _make_coordinator()
        coordinator._client.session.is_authenticated = False
        coordinator._client.login = AsyncMock()

        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(return_value=[])
        coordinator._devices_api = MagicMock()
        coordinator._devices_api.get_devices_snapshot = AsyncMock(return_value=[])

        await coordinator._async_update_data()
        coordinator._client.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_data_filters_spaces_by_id(self) -> None:
        coordinator = _make_coordinator()
        coordinator._client.session.is_authenticated = True

        space_s1 = _make_space("s1")
        space_s2 = _make_space("s2")

        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(return_value=[space_s1, space_s2])
        coordinator._devices_api = MagicMock()
        coordinator._devices_api.get_devices_snapshot = AsyncMock(return_value=[])

        result = await coordinator._async_update_data()
        assert "s1" in result["spaces"]
        assert "s2" not in result["spaces"]

    @pytest.mark.asyncio
    async def test_update_data_raises_update_failed_on_error(self) -> None:
        from homeassistant.helpers.update_coordinator import UpdateFailed

        coordinator = _make_coordinator()
        coordinator._client.session.is_authenticated = True

        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(side_effect=RuntimeError("API error"))

        with pytest.raises(UpdateFailed, match="Error fetching Ajax data"):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_async_shutdown_calls_client_close(self) -> None:
        coordinator = _make_coordinator(space_ids=[])
        coordinator._client.close = AsyncMock()

        await coordinator.async_shutdown()
        coordinator._client.close.assert_called_once()
