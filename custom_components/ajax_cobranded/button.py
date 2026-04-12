"""Button entities for Ajax Security (photo on-demand trigger)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.camera import CAMERA_DEVICE_TYPES
from custom_components.ajax_cobranded.const import DOMAIN, MANUFACTURER
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities = [
        AjaxCapturePhotoButton(
            coordinator=coordinator,
            device_id=device_id,
            hub_id=device.hub_id,
            device_type=device.device_type,
        )
        for device_id, device in coordinator.devices.items()
        if device.device_type in CAMERA_DEVICE_TYPES
    ]
    async_add_entities(entities)


class AjaxCapturePhotoButton(CoordinatorEntity[AjaxCobrandedCoordinator], ButtonEntity):
    """Button to trigger photo on-demand capture."""

    _attr_has_entity_name = True
    _attr_translation_key = "capture_photo"
    _attr_icon = "mdi:camera"

    def __init__(
        self,
        coordinator: AjaxCobrandedCoordinator,
        device_id: str,
        hub_id: str,
        device_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._hub_id = hub_id
        self._device_type = device_type
        self._attr_unique_id = f"ajax_cobranded_{device_id}_capture_photo"
        device = coordinator.devices.get(device_id)
        if device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                via_device=(DOMAIN, device.hub_id),
            )

    async def async_press(self) -> None:
        """Trigger photo capture."""
        _LOGGER.debug("Capture photo button pressed for %s", self._device_id)
        await self.coordinator.devices_api.capture_photo(
            self._hub_id, self._device_id, self._device_type
        )
