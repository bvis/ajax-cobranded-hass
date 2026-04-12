"""Ajax Security Home Assistant integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.const import DEFAULT_POLL_INTERVAL
from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
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
        poll_interval=entry.options.get("poll_interval", DEFAULT_POLL_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Start FCM push notifications if configured
    await coordinator.async_start_push_notifications(
        fcm_project_id=entry.options.get("fcm_project_id", ""),
        fcm_app_id=entry.options.get("fcm_app_id", ""),
        fcm_api_key=entry.options.get("fcm_api_key", ""),
        fcm_sender_id=entry.options.get("fcm_sender_id", ""),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AjaxCobrandedConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: AjaxCobrandedCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok
