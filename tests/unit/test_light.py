"""Tests for light entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.light import LIGHT_DEVICE_TYPES, AjaxLight


class TestLightDeviceTypes:
    def test_dimmer_is_light(self) -> None:
        assert "light_switch_dimmer" in LIGHT_DEVICE_TYPES


class TestAjaxLight:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.unique_id == "ajax_cobranded_d1_light_1"

    def test_has_brightness_support(self) -> None:
        from homeassistant.components.light import ColorMode  # type: ignore[attr-defined]

        coordinator = MagicMock()
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert ColorMode.BRIGHTNESS in light.supported_color_modes

    def test_name_is_none(self) -> None:
        """Light is the primary entity and adopts device name."""
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.name = "Living Room Dimmer"
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light._attr_name is None

    def test_device_info_with_device(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.id = "d1"
        mock_device.name = "Living Room Dimmer"
        mock_device.device_type = "light_switch_dimmer"
        mock_device.hub_id = "h1"
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light._attr_device_info is not None
        assert ("ajax_cobranded", "d1") in light._attr_device_info["identifiers"]

    def test_device_info_without_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert not hasattr(light, "_attr_device_info") or light._attr_device_info is None

    def test_available_when_device_online(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.is_online = True
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.available is True

    def test_unavailable_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.available is False

    def test_is_on_when_brightness_gt_zero(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"brightness_ch1": 50}
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.is_on is True

    def test_is_off_when_brightness_zero(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"brightness_ch1": 0}
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.is_on is False

    def test_is_on_returns_none_when_no_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.is_on is None

    def test_brightness_value(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"brightness_ch1": 100}
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        # 100% -> 255
        assert light.brightness == 255

    def test_brightness_returns_none_when_no_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        assert light.brightness is None

    def test_brightness_partial(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.statuses = {"brightness_ch1": 50}
        coordinator.devices = {"d1": mock_device}
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        # 50% -> ~128
        assert light.brightness == round(50 * 255 / 100)

    @pytest.mark.asyncio
    async def test_turn_on_sends_brightness_command(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        await light.async_turn_on()
        coordinator.devices_api.send_command.assert_called_once()
        cmd = coordinator.devices_api.send_command.call_args[0][0]
        assert cmd.action == "brightness"
        assert cmd.brightness == 100

    @pytest.mark.asyncio
    async def test_turn_on_with_brightness_kwarg(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        # 128/255 * 100 ≈ 50
        await light.async_turn_on(brightness=128)
        cmd = coordinator.devices_api.send_command.call_args[0][0]
        assert cmd.action == "brightness"
        assert cmd.brightness == round(128 * 100 / 255)

    @pytest.mark.asyncio
    async def test_turn_off_sends_zero_brightness(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        light = AjaxLight(
            coordinator=coordinator,
            device_id="d1",
            hub_id="h1",
            device_type="light_switch_dimmer",
            channel=1,
        )
        await light.async_turn_off()
        cmd = coordinator.devices_api.send_command.call_args[0][0]
        assert cmd.action == "brightness"
        assert cmd.brightness == 0
