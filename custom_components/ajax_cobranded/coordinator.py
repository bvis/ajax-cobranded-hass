"""Data update coordinator for Ajax Security."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.security import SecurityApi
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import DOMAIN

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
        poll_interval: int = 30,
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

    @property
    def security_api(self) -> SecurityApi:
        return self._security_api

    @property
    def devices_api(self) -> DevicesApi:
        return self._devices_api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            # Login if not authenticated
            if not self._client.session.is_authenticated:
                await self._client.login()

            # Refresh spaces
            all_spaces = await self._spaces_api.list_spaces()
            self.spaces = {s.id: s for s in all_spaces if s.id in self._space_ids}

            # Refresh devices for each space
            all_devices: dict[str, Device] = {}
            for space_id in self.spaces:
                space_devices = await self._devices_api.get_devices_snapshot(space_id)
                for device in space_devices:
                    all_devices[device.id] = device
            self.devices = all_devices

            return {"spaces": self.spaces, "devices": self.devices}
        except Exception as err:
            raise UpdateFailed("Error fetching Ajax data") from err

    async def async_start_push_notifications(self) -> None:
        """Start FCM push notification listener."""
        from custom_components.ajax_cobranded.notification import (
            AjaxNotificationListener,  # noqa: PLC0415
        )

        self._notification_listener = AjaxNotificationListener(hass=self.hass, coordinator=self)
        await self._notification_listener.async_start()

    async def async_shutdown(self) -> None:
        if self._notification_listener:
            await self._notification_listener.async_stop()
        await self._client.close()
