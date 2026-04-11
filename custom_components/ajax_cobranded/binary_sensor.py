"""Binary sensor entities for Ajax Security."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN, MANUFACTURER
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ajax_cobranded.api.models import Device

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BinarySensorTypeInfo:
    device_class: BinarySensorDeviceClass


BINARY_SENSOR_TYPES: dict[str, BinarySensorTypeInfo] = {
    "door_opened": BinarySensorTypeInfo(BinarySensorDeviceClass.DOOR),
    "motion_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOTION),
    "smoke_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.SMOKE),
    "leak_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOISTURE),
    "tamper": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER),
    "co_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.CO),
    "high_temperature": BinarySensorTypeInfo(BinarySensorDeviceClass.HEAT),
}

_DEVICE_TYPE_SENSORS: dict[str, list[str]] = {
    "door_protect": ["door_opened", "tamper"],
    "door_protect_plus": ["door_opened", "tamper"],
    "door_protect_fibra": ["door_opened", "tamper"],
    "motion_protect": ["motion_detected", "tamper"],
    "motion_protect_plus": ["motion_detected", "tamper"],
    "motion_cam": ["motion_detected", "tamper"],
    "motion_cam_outdoor": ["motion_detected", "tamper"],
    "combi_protect": ["motion_detected", "tamper"],
    "fire_protect": ["smoke_detected", "high_temperature", "tamper"],
    "fire_protect_2": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "fire_protect_plus": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "leaks_protect": ["leak_detected", "tamper"],
    "glass_protect": ["tamper"],
    "motion_cam_phod": ["motion_detected", "tamper"],
    "keypad_combi": ["tamper"],
    "hub_two_4g": [],
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities: list[AjaxBinarySensor] = []
    for device_id, device in coordinator.devices.items():
        sensor_keys = _DEVICE_TYPE_SENSORS.get(device.device_type, ["tamper"])
        for key in sensor_keys:
            if key in BINARY_SENSOR_TYPES:
                entities.append(
                    AjaxBinarySensor(coordinator=coordinator, device_id=device_id, status_key=key)
                )
    async_add_entities(entities)


class AjaxBinarySensor(CoordinatorEntity[AjaxCobrandedCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AjaxCobrandedCoordinator, device_id: str, status_key: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._status_key = status_key
        self._type_info = BINARY_SENSOR_TYPES[status_key]
        self._attr_unique_id = f"ajax_cobranded_{device_id}_{status_key}"
        self._attr_device_class = self._type_info.device_class
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
    def is_on(self) -> bool:
        device = self._device
        if device is None:
            return False
        return bool(device.statuses.get(self._status_key, False))
