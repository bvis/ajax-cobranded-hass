"""Camera entities for Ajax Security (MotionCam photo on demand)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.camera import Camera
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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

CAMERA_DEVICE_TYPES = {"motion_cam_phod", "motion_cam", "motion_cam_outdoor"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities = [
        AjaxCamera(
            coordinator=coordinator,
            device_id=device_id,
            hub_id=device.hub_id,
            device_type=device.device_type,
        )
        for device_id, device in coordinator.devices.items()
        if device.device_type in CAMERA_DEVICE_TYPES
    ]
    async_add_entities(entities)


class AjaxCamera(CoordinatorEntity[AjaxCobrandedCoordinator], Camera):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: AjaxCobrandedCoordinator,
        device_id: str,
        hub_id: str,
        device_type: str,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._device_id = device_id
        self._hub_id = hub_id
        self._device_type = device_type
        self._attr_unique_id = f"ajax_cobranded_{device_id}_camera"
        self._last_image_url: str | None = None
        self._last_image: bytes | None = None
        device = coordinator.devices.get(device_id)
        if device:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, device.id)},
                name=device.name,
                manufacturer=MANUFACTURER,
                model=device.device_type.replace("_", " ").title(),
                via_device=(DOMAIN, device.hub_id),
            )

    @property
    def _device(self) -> Device | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,  # noqa: ARG002
    ) -> bytes | None:
        """Capture a new photo and return image bytes."""
        import aiohttp  # noqa: PLC0415

        # Trigger capture via v2
        result = await self.coordinator.devices_api.capture_photo(
            self._hub_id, self._device_id, self._device_type
        )
        if result and self.coordinator.notification_listener:
            # Wait for the photo URL from push notification
            url = await self.coordinator.notification_listener.wait_for_photo_url(
                self._device_id, timeout=15.0
            )
            if url:
                self._last_image_url = url
                session = async_get_clientsession(self.hass)
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            self._last_image = await resp.read()
                except Exception:
                    _LOGGER.exception("Failed to download photo")
        return self._last_image
