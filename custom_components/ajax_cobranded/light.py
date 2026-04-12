"""Light entities for Ajax Security."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from homeassistant.components.light import (  # type: ignore[attr-defined]
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.api.models import DeviceCommand
from custom_components.ajax_cobranded.const import DOMAIN, MANUFACTURER
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ajax_cobranded.api.models import Device

_LOGGER = logging.getLogger(__name__)

LIGHT_DEVICE_TYPES = {"light_switch_dimmer"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities: list[AjaxLight] = []
    for device_id, device in coordinator.devices.items():
        if device.device_type in LIGHT_DEVICE_TYPES:
            entities.append(
                AjaxLight(
                    coordinator=coordinator,
                    device_id=device_id,
                    hub_id=device.hub_id,
                    device_type=device.device_type,
                    channel=1,
                )
            )
    async_add_entities(entities)


class AjaxLight(CoordinatorEntity[AjaxCobrandedCoordinator], LightEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: AjaxCobrandedCoordinator,
        device_id: str,
        hub_id: str,
        device_type: str,
        channel: int,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._hub_id = hub_id
        self._device_type = device_type
        self._channel = channel
        self._attr_unique_id = f"ajax_cobranded_{device_id}_light_{channel}"
        device = coordinator.devices.get(device_id)
        if device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                via_device=(DOMAIN, f"hub_{device.hub_id}"),
            )

    @property
    def _device(self) -> Device | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    @property
    def is_on(self) -> bool | None:
        device = self._device
        if device is None:
            return None
        brightness_val = device.statuses.get(f"brightness_ch{self._channel}", 0)
        return bool(brightness_val > 0)

    @property
    def brightness(self) -> int | None:
        device = self._device
        if device is None:
            return None
        pct = device.statuses.get(f"brightness_ch{self._channel}", 0)
        return int(round(pct * 255 / 100))

    async def async_turn_on(self, **kwargs: object) -> None:
        brightness_pct = 100
        if ATTR_BRIGHTNESS in kwargs:
            brightness_pct = round(cast("int", kwargs[ATTR_BRIGHTNESS]) * 100 / 255)
        cmd = DeviceCommand.set_brightness(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            brightness=brightness_pct,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        cmd = DeviceCommand.set_brightness(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            brightness=0,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()
