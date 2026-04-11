"""Tests for switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.switch import SWITCH_DEVICE_TYPES, AjaxSwitch


class TestSwitchDeviceTypes:
    def test_relay_is_switch(self) -> None:
        assert "relay" in SWITCH_DEVICE_TYPES

    def test_wall_switch_is_switch(self) -> None:
        assert "wall_switch" in SWITCH_DEVICE_TYPES

    def test_socket_is_switch(self) -> None:
        assert "socket" in SWITCH_DEVICE_TYPES

    def test_light_switch_two_gang_has_two_channels(self) -> None:
        assert SWITCH_DEVICE_TYPES["light_switch_two_gang"] == 2


class TestAjaxSwitch:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.unique_id == "ajax_cobranded_d1_switch_1"

    def test_turn_on_callable(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert hasattr(sw, "async_turn_on")

    def test_turn_off_callable(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert hasattr(sw, "async_turn_off")

    def test_single_channel_name_is_none(self) -> None:
        """Single-channel switch is the primary entity and adopts device name."""
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.name = "Garage Relay"
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw._attr_name is None

    def test_multi_channel_uses_translation_key(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.name = "Wall Switch"
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_two_gang",
            channel=2,
        )
        assert sw._attr_translation_key == "channel_2"

    def test_device_info_with_device(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.id = "d1"
        mock_device.name = "Relay"
        mock_device.device_type = "relay"
        mock_device.hub_id = "h1"
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw._attr_device_info is not None
        assert ("ajax_cobranded", "d1") in sw._attr_device_info["identifiers"]

    def test_device_info_without_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert not hasattr(sw, "_attr_device_info") or sw._attr_device_info is None

    def test_available_when_online(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.is_online = True
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.available is True

    def test_unavailable_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.available is False

    def test_is_on_true(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"switch_ch1": True}
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.is_on is True

    def test_is_on_false(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"switch_ch1": False}
        coordinator.devices = {"d1": mock_device}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.is_on is False

    def test_is_on_returns_none_when_no_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        assert sw.is_on is None

    @pytest.mark.asyncio
    async def test_turn_on_sends_command(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        await sw.async_turn_on()
        coordinator.devices_api.send_command.assert_called_once()
        cmd = coordinator.devices_api.send_command.call_args[0][0]
        assert cmd.action == "on"

    @pytest.mark.asyncio
    async def test_turn_off_sends_command(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="relay", channel=1
        )
        await sw.async_turn_off()
        coordinator.devices_api.send_command.assert_called_once()
        cmd = coordinator.devices_api.send_command.call_args[0][0]
        assert cmd.action == "off"
