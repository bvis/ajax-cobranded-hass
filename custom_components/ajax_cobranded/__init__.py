"""Ajax Security Home Assistant integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import ServiceCall

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.const import DEFAULT_POLL_INTERVAL, DOMAIN
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


async def _async_handle_force_arm(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle force_arm service call (arm ignoring open sensors)."""
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        coordinator: AjaxCobrandedCoordinator = entry.runtime_data
        for space_id in coordinator._space_ids:
            await coordinator.security_api.arm(space_id, ignore_alarms=True)
        await coordinator.async_request_refresh()


async def _async_handle_force_arm_night(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle force_arm_night service call (night mode ignoring open sensors)."""
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        coordinator: AjaxCobrandedCoordinator = entry.runtime_data
        for space_id in coordinator._space_ids:
            await coordinator.security_api.arm_night_mode(space_id, ignore_alarms=True)
        await coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: AjaxCobrandedConfigEntry) -> bool:
    # Migrate plaintext password to hash (one-time migration)
    if "password" in entry.data and "password_hash" not in entry.data:
        from custom_components.ajax_cobranded.api.session import AjaxSession  # noqa: PLC0415

        new_data = dict(entry.data)
        new_data["password_hash"] = AjaxSession.hash_password(new_data.pop("password"))
        hass.config_entries.async_update_entry(entry, data=new_data)
        _LOGGER.warning(
            "Migrated plaintext password to hash for entry %s. Please reconfigure if issues arise.",
            entry.entry_id,
        )

    # Support legacy entries that stored plaintext password instead of hash
    if "password_hash" in entry.data:
        client = AjaxGrpcClient(
            email=entry.data["email"],
            password_hash=entry.data["password_hash"],
            device_id=entry.data.get("device_id"),
            app_label=entry.data.get("app_label", ""),
        )
    else:
        _LOGGER.warning(
            "Entry %s has neither password_hash nor password. Authentication may fail.",
            entry.entry_id,
        )
        client = AjaxGrpcClient(
            email=entry.data["email"],
            password=entry.data.get("password", ""),
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

    async def _force_arm_handler(call: ServiceCall) -> None:
        await _async_handle_force_arm(hass, call)

    async def _force_arm_night_handler(call: ServiceCall) -> None:
        await _async_handle_force_arm_night(hass, call)

    if not hass.services.has_service(DOMAIN, "force_arm"):
        hass.services.async_register(DOMAIN, "force_arm", _force_arm_handler)
        hass.services.async_register(DOMAIN, "force_arm_night", _force_arm_night_handler)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AjaxCobrandedConfigEntry) -> bool:
    remaining = hass.config_entries.async_entries(DOMAIN)
    if not any(e.entry_id != entry.entry_id for e in remaining):
        hass.services.async_remove(DOMAIN, "force_arm")
        hass.services.async_remove(DOMAIN, "force_arm_night")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: AjaxCobrandedCoordinator = entry.runtime_data
        await coordinator.async_shutdown()
    return unload_ok
