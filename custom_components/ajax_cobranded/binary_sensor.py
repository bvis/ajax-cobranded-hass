"""Binary sensor entities for Ajax Security."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
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
    translation_key: str | None = None


BINARY_SENSOR_TYPES: dict[str, BinarySensorTypeInfo] = {
    "door_opened": BinarySensorTypeInfo(BinarySensorDeviceClass.DOOR),
    "motion_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOTION),
    "smoke_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.SMOKE),
    "leak_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOISTURE),
    "tamper": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER),
    "co_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.CO),
    "high_temperature": BinarySensorTypeInfo(BinarySensorDeviceClass.HEAT),
    "monitoring_active": BinarySensorTypeInfo(BinarySensorDeviceClass.CONNECTIVITY, "monitoring"),
    "gsm_connected": BinarySensorTypeInfo(BinarySensorDeviceClass.CONNECTIVITY, "gsm"),
    "lid_opened": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER, "lid"),
    "external_contact_broken": BinarySensorTypeInfo(BinarySensorDeviceClass.PROBLEM, "ext_contact"),
    "external_contact_alert": BinarySensorTypeInfo(BinarySensorDeviceClass.SAFETY, "ext_alert"),
    "case_drilling": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER, "drilling"),
    "anti_masking": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER, "anti_mask"),
    "malfunction": BinarySensorTypeInfo(BinarySensorDeviceClass.PROBLEM, "malfunction"),
    "interference": BinarySensorTypeInfo(BinarySensorDeviceClass.PROBLEM, "interference"),
    "relay_stuck": BinarySensorTypeInfo(BinarySensorDeviceClass.PROBLEM, "relay_stuck"),
    "always_active": BinarySensorTypeInfo(BinarySensorDeviceClass.RUNNING, "always_active"),
}

_DEVICE_TYPE_SENSORS: dict[str, list[str]] = {
    "door_protect": ["door_opened", "tamper"],
    "door_protect_plus": ["door_opened", "tamper", "external_contact_broken"],
    "door_protect_fibra": ["door_opened", "tamper"],
    "door_protect_s": ["door_opened", "tamper"],
    "door_protect_s_plus": ["door_opened", "tamper", "external_contact_broken"],
    "door_protect_plus_fibra": ["door_opened", "tamper", "external_contact_broken"],
    "door_protect_g3": ["door_opened", "tamper"],
    "motion_protect": ["motion_detected", "tamper"],
    "motion_protect_plus": ["motion_detected", "tamper"],
    "motion_protect_fibra": ["motion_detected", "tamper"],
    "motion_protect_outdoor": ["motion_detected", "tamper"],
    "motion_protect_curtain": ["motion_detected", "tamper"],
    "motion_cam": ["motion_detected", "tamper"],
    "motion_cam_outdoor": ["motion_detected", "tamper"],
    "motion_cam_fibra": ["motion_detected", "tamper"],
    "motion_cam_phod": ["motion_detected", "tamper"],
    "combi_protect": ["motion_detected", "tamper"],
    "combi_protect_s": ["motion_detected", "tamper"],
    "combi_protect_fibra": ["motion_detected", "tamper"],
    "glass_protect": ["tamper"],
    "glass_protect_s": ["tamper"],
    "glass_protect_fibra": ["tamper"],
    "fire_protect": ["smoke_detected", "high_temperature", "tamper"],
    "fire_protect_plus": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "fire_protect_2": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "leaks_protect": ["leak_detected", "tamper"],
    "home_siren": ["tamper"],
    "home_siren_s": ["tamper"],
    "home_siren_fibra": ["tamper"],
    "street_siren": ["tamper"],
    "street_siren_plus": ["tamper"],
    "street_siren_fibra": ["tamper"],
    "street_siren_double_deck": ["tamper"],
    "rex": [],
    "rex_2": [],
    "transmitter": ["tamper"],
    "multi_transmitter": ["tamper"],
    "multi_transmitter_fibra": ["tamper"],
    "life_quality": [],
    "water_stop": [],
    "keypad_combi": ["tamper"],
    "hub_two_4g": ["monitoring_active", "gsm_connected", "lid_opened"],
    "hub": ["monitoring_active", "gsm_connected", "lid_opened"],
    "hub_plus": ["monitoring_active", "gsm_connected", "lid_opened"],
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities: list[AjaxBinarySensor | AjaxConnectivitySensor | AjaxProblemSensor] = []
    for device_id, device in coordinator.devices.items():
        sensor_keys = _DEVICE_TYPE_SENSORS.get(device.device_type, ["tamper"])
        for key in sensor_keys:
            if key in BINARY_SENSOR_TYPES:
                entities.append(
                    AjaxBinarySensor(coordinator=coordinator, device_id=device_id, status_key=key)
                )
        entities.append(AjaxConnectivitySensor(coordinator=coordinator, device_id=device_id))
        entities.append(AjaxProblemSensor(coordinator=coordinator, device_id=device_id))
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
        self._attr_translation_key = self._type_info.translation_key
        device = coordinator.devices.get(device_id)
        if device:
            is_hub = device.device_type.startswith("hub")
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                **({} if is_hub else {"via_device": (DOMAIN, device.hub_id)}),
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._device
        if device is None or self._status_key != "motion_detected":
            return {}
        detected_at = device.statuses.get("motion_detected_at")
        if detected_at is not None:
            return {"detected_at": detected_at}
        return {}


class AjaxConnectivitySensor(CoordinatorEntity[AjaxCobrandedCoordinator], BinarySensorEntity):
    """Binary sensor reporting per-device online/offline connectivity."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connectivity"

    def __init__(self, coordinator: AjaxCobrandedCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"ajax_cobranded_{device_id}_connectivity"
        device = coordinator.devices.get(device_id)
        if device:
            is_hub = device.device_type.startswith("hub")
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                **({} if is_hub else {"via_device": (DOMAIN, device.hub_id)}),
            )

    @property
    def is_on(self) -> bool:
        device = self.coordinator.devices.get(self._device_id)
        return device is not None and device.is_online


class AjaxProblemSensor(CoordinatorEntity[AjaxCobrandedCoordinator], BinarySensorEntity):
    """Binary sensor reporting per-device malfunction/problem state."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "problem"

    def __init__(self, coordinator: AjaxCobrandedCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"ajax_cobranded_{device_id}_problem"
        device = coordinator.devices.get(device_id)
        if device:
            is_hub = device.device_type.startswith("hub")
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                **({} if is_hub else {"via_device": (DOMAIN, device.hub_id)}),
            )

    @property
    def is_on(self) -> bool:
        device = self.coordinator.devices.get(self._device_id)
        return device is not None and device.malfunctions > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self.coordinator.devices.get(self._device_id)
        if device:
            return {"malfunctions_count": device.malfunctions}
        return {}
