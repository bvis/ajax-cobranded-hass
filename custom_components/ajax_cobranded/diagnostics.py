"""Diagnostics support for Ajax Security."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD

from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

type AjaxCobrandedConfigEntry = ConfigEntry[AjaxCobrandedCoordinator]

TO_REDACT = {CONF_PASSWORD, "password_hash", "email", "session_token", "device_id", "push_token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: AjaxCobrandedConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "spaces": {
            sid: {
                "name": s.name,
                "security_state": s.security_state.name,
                "online": s.is_online,
                "malfunctions": s.malfunctions_count,
            }
            for sid, s in coordinator.spaces.items()
        },
        "devices": {
            did: {
                "name": d.name,
                "type": d.device_type,
                "state": d.state,
                "online": d.is_online,
                "malfunctions": d.malfunctions,
                "bypassed": d.bypassed,
                "battery": (
                    {"level": d.battery.level, "low": d.battery.is_low} if d.battery else None
                ),
                "statuses": list(d.statuses.keys()),
            }
            for did, d in coordinator.devices.items()
        },
        "stream_tasks": len(coordinator._stream_tasks),
        "notification_listener": coordinator.notification_listener is not None,
    }
