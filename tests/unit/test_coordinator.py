"""Tests for the data update coordinator."""

from __future__ import annotations

import asyncio
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
        # Mark streams already started so fallback polling runs
        coordinator._streams_started = True

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


class TestStreamHandlers:
    """Tests for coordinator stream callback handlers."""

    def _make_coordinator_with_stream(self) -> AjaxCobrandedCoordinator:  # noqa: F821
        from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

        hass = MagicMock()
        client = MagicMock()
        with patch(
            "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
            return_value=None,
        ):
            coordinator = AjaxCobrandedCoordinator(
                hass=hass, client=client, space_ids=["s1"], poll_interval=300
            )
        coordinator.async_set_updated_data = MagicMock()
        return coordinator

    def test_handle_devices_snapshot_populates_devices(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        device = _make_device("d1")
        coordinator._handle_devices_snapshot([device])
        assert "d1" in coordinator.devices
        coordinator.async_set_updated_data.assert_called_once()

    def test_handle_devices_snapshot_overwrites_existing(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")
        updated = _make_device("d1")
        coordinator._handle_devices_snapshot([updated])
        assert coordinator.devices["d1"] is updated

    def test_handle_status_update_add_sets_status_true(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "door_opened", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("door_opened") is True
        coordinator.async_set_updated_data.assert_called_once()

    def test_handle_status_update_remove_deletes_status(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        device = Device(
            id="d1",
            hub_id="hub-1",
            name="Sensor",
            device_type="door_protect",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={"door_opened": True},
            battery=None,
        )
        coordinator.devices["d1"] = device

        coordinator._handle_status_update("d1", "door_opened", {"op": 3})

        assert "door_opened" not in coordinator.devices["d1"].statuses
        coordinator.async_set_updated_data.assert_called_once()

    def test_handle_status_update_co_level_maps_to_co_detected(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "co_level_detected", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("co_detected") is True

    def test_handle_status_update_high_temp_maps_correctly(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "high_temperature_detected", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("high_temperature") is True

    def test_handle_status_update_case_drilling_maps_correctly(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "case_drilling_detected", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("case_drilling") is True

    def test_handle_status_update_anti_masking_maps_correctly(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "anti_masking_alert", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("anti_masking") is True

    def test_handle_status_update_interference_maps_correctly(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator.devices["d1"] = _make_device("d1")

        coordinator._handle_status_update("d1", "interference_detected", {"op": 1})

        assert coordinator.devices["d1"].statuses.get("interference") is True

    def test_handle_status_update_unknown_device_is_ignored(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        # No devices in coordinator
        coordinator._handle_status_update("nonexistent", "door_opened", {"op": 1})
        coordinator.async_set_updated_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_stream_tasks(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator._client.close = AsyncMock()

        # Create a real task that runs forever
        async def _forever() -> None:
            await asyncio.sleep(9999)

        task = asyncio.create_task(_forever())
        coordinator._stream_tasks.append(task)

        await coordinator.async_shutdown()

        assert task.cancelled()
        coordinator._client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_first_update_starts_streams(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator._client.session.is_authenticated = True

        space = _make_space("s1")
        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(return_value=[space])
        coordinator.spaces = {"s1": space}

        mock_task = MagicMock(spec=asyncio.Task)
        coordinator._devices_api = MagicMock()
        coordinator._devices_api.start_device_stream = AsyncMock(return_value=mock_task)

        result = await coordinator._async_update_data()

        coordinator._devices_api.start_device_stream.assert_called_once_with(
            "s1",
            on_devices_snapshot=coordinator._handle_devices_snapshot,
            on_status_update=coordinator._handle_status_update,
        )
        assert coordinator._streams_started is True
        assert mock_task in coordinator._stream_tasks
        assert "spaces" in result

    @pytest.mark.asyncio
    async def test_second_update_does_not_restart_streams(self) -> None:
        coordinator = self._make_coordinator_with_stream()
        coordinator._client.session.is_authenticated = True
        coordinator._streams_started = True  # already started

        space = _make_space("s1")
        coordinator._spaces_api = MagicMock()
        coordinator._spaces_api.list_spaces = AsyncMock(return_value=[space])
        coordinator.spaces = {"s1": space}

        coordinator._devices_api = MagicMock()
        coordinator._devices_api.get_devices_snapshot = AsyncMock(return_value=[])

        await coordinator._async_update_data()

        coordinator._devices_api.start_device_stream = MagicMock()
        coordinator._devices_api.start_device_stream.assert_not_called()
