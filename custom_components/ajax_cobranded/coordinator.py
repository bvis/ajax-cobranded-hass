"""Data update coordinator for Ajax Security."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.models import Device as DeviceModel
from custom_components.ajax_cobranded.api.security import SecurityApi
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import DEFAULT_POLL_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
    from custom_components.ajax_cobranded.api.models import Device, Space
    from custom_components.ajax_cobranded.notification import AjaxNotificationListener

_LOGGER = logging.getLogger(__name__)


class AjaxCobrandedCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        client: AjaxGrpcClient,
        space_ids: list[str],
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=poll_interval)
        )
        self._client = client
        self._space_ids = space_ids
        self._spaces_api = SpacesApi(client)
        self._security_api = SecurityApi(client)
        self._devices_api = DevicesApi(client)
        self.spaces: dict[str, Space] = {}
        self.devices: dict[str, Device] = {}
        self._notification_listener: AjaxNotificationListener | None = None
        self._stream_tasks: list[asyncio.Task[None]] = []
        self._streams_started: bool = False

    @property
    def security_api(self) -> SecurityApi:
        return self._security_api

    @property
    def devices_api(self) -> DevicesApi:
        return self._devices_api

    @property
    def notification_listener(self) -> AjaxNotificationListener | None:
        return self._notification_listener

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Login if not authenticated
            if not self._client.session.is_authenticated:
                await self._client.login()

            # Refresh spaces
            all_spaces = await self._spaces_api.list_spaces()
            self.spaces = {s.id: s for s in all_spaces if s.id in self._space_ids}

            # Start persistent device streams on first update (once only)
            if not self._streams_started:
                self._streams_started = True
                await self._start_device_streams()
                # Devices are populated by the stream snapshot callback;
                # return current (possibly empty) state on this first poll.
                return {"spaces": self.spaces, "devices": self.devices}

            # Fallback poll: refresh devices from snapshot for each space
            all_devices: dict[str, Device] = {}
            for space_id in self.spaces:
                space_devices = await self._devices_api.get_devices_snapshot(space_id)
                for device in space_devices:
                    all_devices[device.id] = device
            self.devices = all_devices

            return {"spaces": self.spaces, "devices": self.devices}
        except Exception as err:
            raise UpdateFailed("Error fetching Ajax data") from err

    async def _start_device_streams(self) -> None:
        """Start persistent device streams for all spaces."""
        for space_id in self._space_ids:
            try:
                task = await self._devices_api.start_device_stream(
                    space_id,
                    on_devices_snapshot=self._handle_devices_snapshot,
                    on_status_update=self._handle_status_update,
                )
                self._stream_tasks.append(task)
                _LOGGER.debug("Device stream started for space %s", space_id)
            except Exception:
                _LOGGER.exception("Failed to start device stream for space %s", space_id)

    def _handle_devices_snapshot(self, devices: list[Device]) -> None:
        """Handle initial snapshot or full device snapshot update from stream."""
        for device in devices:
            self.devices[device.id] = device
        self.async_set_updated_data({"spaces": self.spaces, "devices": self.devices})

    def _handle_status_update(self, device_id: str, status_name: str, data: dict[str, Any]) -> None:
        """Handle real-time status update from the persistent stream.

        data contains {"op": int} where 1=ADD, 2=UPDATE, 3=REMOVE.
        """
        device = self.devices.get(device_id)
        if not device:
            _LOGGER.debug("Status update for unknown device %s (status=%s)", device_id, status_name)
            return

        op = data.get("op", 2)
        new_statuses = dict(device.statuses)

        # Map proto status field name to internal key used by binary_sensor/sensor
        _status_key_map = {
            "co_level_detected": "co_detected",
            "high_temperature_detected": "high_temperature",
            "case_drilling_detected": "case_drilling",
            "anti_masking_alert": "anti_masking",
            "interference_detected": "interference",
        }
        key = _status_key_map.get(status_name, status_name)
        _LOGGER.debug(
            "Status update: device=%s status=%s key=%s op=%s",
            device_id,
            status_name,
            key,
            op,
        )

        if op == 3:  # REMOVE
            new_statuses.pop(key, None)
        else:  # ADD (1) or UPDATE (2)
            new_statuses[key] = True

        updated = DeviceModel(
            id=device.id,
            hub_id=device.hub_id,
            name=device.name,
            device_type=device.device_type,
            room_id=device.room_id,
            group_id=device.group_id,
            state=device.state,
            malfunctions=device.malfunctions,
            bypassed=device.bypassed,
            statuses=new_statuses,
            battery=device.battery,
        )
        self.devices[device.id] = updated
        self.async_set_updated_data({"spaces": self.spaces, "devices": self.devices})

    async def async_start_push_notifications(
        self,
        *,
        fcm_project_id: str = "",
        fcm_app_id: str = "",
        fcm_api_key: str = "",
        fcm_sender_id: str = "",
    ) -> None:
        """Start FCM push notification listener."""
        from custom_components.ajax_cobranded.notification import (
            AjaxNotificationListener,  # noqa: PLC0415
        )

        self._notification_listener = AjaxNotificationListener(
            hass=self.hass,
            coordinator=self,
            fcm_project_id=fcm_project_id,
            fcm_app_id=fcm_app_id,
            fcm_api_key=fcm_api_key,
            fcm_sender_id=fcm_sender_id,
        )
        await self._notification_listener.async_start()

    async def async_shutdown(self) -> None:
        # Cancel all stream tasks
        for task in self._stream_tasks:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._stream_tasks.clear()

        if self._notification_listener:
            await self._notification_listener.async_stop()
        await self._client.close()
