"""Event platform for Ajax Security."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.event import EventEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import ALL_EVENT_TYPES, DOMAIN, MANUFACTURER
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
        AjaxSecurityEvent(coordinator=coordinator, space_id=space_id)
        for space_id in coordinator.spaces
    ]
    async_add_entities(entities)
    for entity in entities:
        coordinator.register_event_entity(entity._space_id, entity)


class AjaxSecurityEvent(CoordinatorEntity[AjaxCobrandedCoordinator], EventEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "security_event"

    def __init__(self, coordinator: AjaxCobrandedCoordinator, space_id: str) -> None:
        super().__init__(coordinator)
        self._space_id = space_id
        space = coordinator.spaces.get(space_id)
        hub_id = space.hub_id if space else space_id
        self._attr_unique_id = f"ajax_cobranded_{hub_id}_event"
        self._attr_event_types = ALL_EVENT_TYPES
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, hub_id)},
            name=space.name if space else "Ajax Hub",
            manufacturer=MANUFACTURER,
            model="Hub",
        )

    @property
    def event_types(self) -> list[str]:
        return self._attr_event_types

    def handle_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Called by coordinator when a push event arrives."""
        if event_type not in ALL_EVENT_TYPES:
            _LOGGER.debug("Ignoring unknown event type: %s", event_type)
            return
        self._trigger_event(event_type, data)
        self.async_write_ha_state()
