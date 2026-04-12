"""Sensor entities for Ajax Security."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN, MANUFACTURER
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ajax_cobranded.api.hub_object import SimCardInfo
    from custom_components.ajax_cobranded.api.models import Device

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SensorTypeInfo:
    device_class: SensorDeviceClass | None
    state_class: SensorStateClass | None
    unit: str | None
    value_source: str
    entity_category: EntityCategory | None
    translation_key: str | None = None
    entity_registry_enabled_default: bool = True


SENSOR_TYPES: dict[str, SensorTypeInfo] = {
    "battery_level": SensorTypeInfo(
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
        PERCENTAGE,
        "battery",
        EntityCategory.DIAGNOSTIC,
    ),
    "temperature": SensorTypeInfo(
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        UnitOfTemperature.CELSIUS,
        "status",
        None,
    ),
    "humidity": SensorTypeInfo(
        SensorDeviceClass.HUMIDITY,
        SensorStateClass.MEASUREMENT,
        PERCENTAGE,
        "status",
        None,
    ),
    "co2": SensorTypeInfo(
        SensorDeviceClass.CO2,
        SensorStateClass.MEASUREMENT,
        "ppm",
        "status",
        None,
    ),
    "signal_strength": SensorTypeInfo(
        None,
        SensorStateClass.MEASUREMENT,
        None,
        "status",
        EntityCategory.DIAGNOSTIC,
        translation_key="signal_level",
        entity_registry_enabled_default=False,
    ),
    "gsm_type": SensorTypeInfo(
        None,
        None,
        None,
        "status",
        EntityCategory.DIAGNOSTIC,
        translation_key="gsm_type",
        entity_registry_enabled_default=True,
    ),
    "wifi_signal_level": SensorTypeInfo(
        None,
        SensorStateClass.MEASUREMENT,
        None,
        "status",
        EntityCategory.DIAGNOSTIC,
        translation_key="wifi_signal_level",
        entity_registry_enabled_default=False,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for device_id, device in coordinator.devices.items():
        if device.battery is not None:
            entities.append(
                AjaxSensor(coordinator=coordinator, device_id=device_id, sensor_key="battery_level")
            )
        _status_sensor_keys = (
            "temperature",
            "humidity",
            "co2",
            "signal_strength",
            "gsm_type",
            "wifi_signal_level",
        )
        for key in _status_sensor_keys:
            if key in device.statuses:
                entities.append(
                    AjaxSensor(coordinator=coordinator, device_id=device_id, sensor_key=key)
                )

    # Add SIM sensors for hub devices that have SIM info
    for space in coordinator.spaces.values():
        if space.hub_id in coordinator.sim_info:
            entities.append(AjaxSimImeiSensor(coordinator=coordinator, hub_id=space.hub_id))

    async_add_entities(entities)


class AjaxSensor(CoordinatorEntity[AjaxCobrandedCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AjaxCobrandedCoordinator, device_id: str, sensor_key: str
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._sensor_key = sensor_key
        self._type_info = SENSOR_TYPES[sensor_key]
        self._attr_unique_id = f"ajax_cobranded_{device_id}_{sensor_key}"
        self._attr_device_class = self._type_info.device_class
        self._attr_state_class = self._type_info.state_class
        self._attr_native_unit_of_measurement = self._type_info.unit
        self._attr_entity_category = self._type_info.entity_category
        self._attr_translation_key = self._type_info.translation_key
        self._attr_entity_registry_enabled_default = self._type_info.entity_registry_enabled_default
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
    def native_value(self) -> float | int | str | None:
        device = self._device
        if device is None:
            return None
        if self._type_info.value_source == "battery" and device.battery:
            return int(device.battery.level)
        raw = device.statuses.get(self._sensor_key)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        return float(raw) if isinstance(raw, float) else int(raw)


class AjaxSimBaseSensor(CoordinatorEntity[AjaxCobrandedCoordinator], SensorEntity):
    """Base class for SIM card sensors attached to a hub device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AjaxCobrandedCoordinator, hub_id: str) -> None:
        super().__init__(coordinator)
        self._hub_id = hub_id
        # Find hub device to populate device_info
        hub_device = coordinator.devices.get(hub_id)
        if hub_device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, hub_id)},
                name=hub_device.name,
                manufacturer=MANUFACTURER,
                model=hub_device.device_type.replace("_", " ").title(),
            )

    @property
    def _sim_info(self) -> SimCardInfo | None:
        return self.coordinator.sim_info.get(self._hub_id)

    @property
    def available(self) -> bool:
        return self._sim_info is not None


class AjaxSimImeiSensor(AjaxSimBaseSensor):
    """Sensor exposing the hub IMEI number."""

    _attr_translation_key = "sim_imei"

    def __init__(self, coordinator: AjaxCobrandedCoordinator, hub_id: str) -> None:
        super().__init__(coordinator, hub_id)
        self._attr_unique_id = f"ajax_cobranded_{hub_id}_sim_imei"

    @property
    def native_value(self) -> str | None:
        sim = self._sim_info
        return sim.imei if sim else None
