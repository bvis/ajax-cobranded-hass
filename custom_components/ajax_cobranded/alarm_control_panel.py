"""Alarm control panel for Ajax Security."""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.alarm_control_panel import (  # type: ignore[attr-defined]
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN, MANUFACTURER, SecurityState
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ajax_cobranded.api.models import Space

_LOGGER = logging.getLogger(__name__)

_STATE_MAP = {
    SecurityState.ARMED: AlarmControlPanelState.ARMED_AWAY,
    SecurityState.DISARMED: AlarmControlPanelState.DISARMED,
    SecurityState.NIGHT_MODE: AlarmControlPanelState.ARMED_NIGHT,
    SecurityState.PARTIALLY_ARMED: AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    SecurityState.AWAITING_EXIT_TIMER: AlarmControlPanelState.ARMING,
    SecurityState.AWAITING_SECOND_STAGE: AlarmControlPanelState.ARMING,
    SecurityState.TWO_STAGE_INCOMPLETE: AlarmControlPanelState.ARMING,
    SecurityState.AWAITING_VDS: AlarmControlPanelState.ARMING,
    SecurityState.NONE: AlarmControlPanelState.DISARMED,
}


def map_security_state(state: SecurityState) -> AlarmControlPanelState:
    return _STATE_MAP.get(state, AlarmControlPanelState.DISARMED)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AjaxCobrandedCoordinator = entry.runtime_data
    entities = [
        AjaxAlarmControlPanel(coordinator=coordinator, space_id=space_id)
        for space_id in coordinator.spaces
    ]
    async_add_entities(entities)


class AjaxAlarmControlPanel(CoordinatorEntity[AjaxCobrandedCoordinator], AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, coordinator: AjaxCobrandedCoordinator, space_id: str) -> None:
        super().__init__(coordinator)
        self._space_id = space_id
        self._attr_unique_id = f"ajax_cobranded_alarm_{space_id}"
        space = coordinator.spaces.get(space_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, space.hub_id if space else space_id)},
            name=space.name if space else "Ajax Hub",
            manufacturer=MANUFACTURER,
            model="Hub",
        )

    def _get_options(self) -> dict[str, Any]:
        """Return config entry options, or empty dict if entry is unavailable."""
        entry = self.coordinator.config_entry
        if entry is None:
            return {}
        return dict(entry.options)

    @property
    def code_arm_required(self) -> bool:
        return bool(self._get_options().get("use_pin_code", False))

    def _validate_code(self, code: str | None) -> None:
        """Raise HomeAssistantError if the provided code does not match the stored hash."""
        if not self.code_arm_required:
            return
        stored_hash = self._get_options().get("pin_code_hash", "")
        if not code or hashlib.sha256(code.encode()).hexdigest() != stored_hash:
            raise HomeAssistantError("Invalid alarm code")

    @property
    def _space(self) -> Space | None:
        return self.coordinator.spaces.get(self._space_id)

    @property
    def available(self) -> bool:
        space = self._space
        return space is not None and space.is_online

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        space = self._space
        if space is None:
            return None
        return map_security_state(space.security_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        space = self._space
        if space is None:
            return {}
        return {
            "hub_id": space.hub_id,
            "malfunctions": space.malfunctions_count,
            "connection_status": space.connection_status.name,
        }

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        self._validate_code(code)
        await self.coordinator.security_api.arm(self._space_id)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        self._validate_code(code)
        await self.coordinator.security_api.arm_night_mode(self._space_id)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        self._validate_code(code)
        await self.coordinator.security_api.disarm(self._space_id)
        await self.coordinator.async_request_refresh()
