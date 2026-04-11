"""Ajax Security Home Assistant integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
]

type AjaxCobrandedConfigEntry = ConfigEntry[AjaxCobrandedCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AjaxCobrandedConfigEntry) -> bool:
    # Support legacy entries that stored plaintext password instead of hash
    if "password_hash" in entry.data:
        client = AjaxGrpcClient(
            email=entry.data["email"],
            password_hash=entry.data["password_hash"],
            device_id=entry.data.get("device_id"),
            app_label=entry.data.get("app_label", ""),
        )
    else:
        client = AjaxGrpcClient(
            email=entry.data["email"],
            password=entry.data["password"],
            device_id=entry.data.get("device_id"),
            app_label=entry.data.get("app_label", ""),
        )
    await client.connect()
    coordinator = AjaxCobrandedCoordinator(
        hass=hass,
        client=client,
        space_ids=entry.data.get("spaces", []),
        poll_interval=entry.options.get("poll_interval", 30),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Start FCM push notifications for real-time updates
    await coordinator.async_start_push_notifications()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AjaxCobrandedConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: AjaxCobrandedCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok
