"""FCM push notification listener for Ajax Security."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from custom_components.ajax_cobranded.const import (
    DOMAIN,
    FCM_API_KEY,
    FCM_APP_ID,
    FCM_PROJECT_ID,
    FCM_SENDER_ID,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from custom_components.ajax_cobranded.coordinator import AjaxCobrandedCoordinator

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}_fcm_credentials"
STORAGE_VERSION = 1


class AjaxNotificationListener:
    """Manages FCM push notification registration and listening."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: AjaxCobrandedCoordinator,
    ) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._push_client: Any = None
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._credentials: dict[str, Any] | None = None

    async def async_start(self) -> None:
        """Register with FCM and start listening for push notifications."""
        try:
            from firebase_messaging import FcmPushClient  # noqa: PLC0415
            from firebase_messaging.fcmregister import (  # noqa: PLC0415
                FcmRegister,
                FcmRegisterConfig,
            )
        except ImportError:
            _LOGGER.debug("firebase_messaging not installed, push notifications disabled")
            return

        # Load or create FCM credentials
        stored = await self._store.async_load()
        self._credentials = dict(stored) if stored else None

        fcm_config = FcmRegisterConfig(
            project_id=FCM_PROJECT_ID,
            app_id=FCM_APP_ID,
            api_key=FCM_API_KEY,
            messaging_sender_id=FCM_SENDER_ID,
        )

        if not self._credentials:
            _LOGGER.debug("Registering with FCM...")
            try:
                registerer = FcmRegister(config=fcm_config)
                raw_result: Any = registerer.register()  # noqa: ANN401
                # register() may be sync or async depending on library version
                import inspect  # noqa: PLC0415

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result
                self._credentials = dict(raw_result)
                await self._store.async_save(self._credentials)
                _LOGGER.debug("FCM registration successful")
            except Exception:
                _LOGGER.exception("FCM registration failed")
                return

        # Extract FCM token and register with Ajax servers
        fcm_data = self._credentials.get("fcm", {})
        registration = fcm_data.get("registration", {}) if isinstance(fcm_data, dict) else {}
        fcm_token = registration.get("token") if isinstance(registration, dict) else None
        if fcm_token:
            _LOGGER.debug("FCM token obtained, registering with Ajax servers")
            await self._register_push_token(str(fcm_token))
        else:
            _LOGGER.debug("No FCM token found in credentials")

        # Start push client
        try:
            self._push_client = FcmPushClient(
                callback=self._on_notification,
                fcm_config=fcm_config,
                credentials=self._credentials,
            )
            start_result = self._push_client.start()
            if hasattr(start_result, "__await__"):
                await start_result
            _LOGGER.debug("FCM push client started for Ajax")
        except Exception:
            _LOGGER.exception("Failed to start FCM push client")

    async def _register_push_token(self, fcm_token: str) -> None:
        """Register the FCM token with Ajax servers via gRPC."""
        proto_path = str(Path(__file__).parent / "proto")
        if proto_path not in sys.path:
            sys.path.append(proto_path)

        try:
            from v3.mobilegwsvc.commonmodels.type import user_role_pb2  # noqa: PLC0415
            from v3.mobilegwsvc.service.upsert_push_token import (  # noqa: PLC0415
                endpoint_pb2_grpc,
                request_pb2,
            )

            client = self._coordinator._client
            channel = client._get_channel()
            metadata = client._session.get_call_metadata()

            stub = endpoint_pb2_grpc.UpsertPushTokenServiceStub(channel)
            request = request_pb2.UpsertPushTokenRequest(
                user_hex_id=client.session.user_hex_id or "",
                user_role=user_role_pb2.USER_ROLE_USER,
                push_token=fcm_token,
                push_token_type=5,  # PUSH_TOKEN_TYPE_AOS_FCM
            )

            response = await stub.execute(request, metadata=metadata, timeout=15)
            if response.HasField("success"):
                _LOGGER.debug("Push token registered with Ajax servers")
            else:
                _LOGGER.debug("Failed to register push token with Ajax servers")
        except Exception:
            _LOGGER.exception("Error registering push token")

    def _on_notification(
        self,
        notification: dict[str, Any],
        persistent_id: str,
        obj: object = None,  # noqa: ARG002
    ) -> None:
        """Handle incoming FCM push notification."""
        _LOGGER.debug(
            "Push notification received: persistent_id=%s data=%s", persistent_id, notification
        )
        if self._hass.loop and self._hass.loop.is_running():
            self._hass.loop.call_soon_threadsafe(
                self._hass.async_create_task,
                self._coordinator.async_request_refresh(),
            )

    async def async_stop(self) -> None:
        """Stop the FCM push client."""
        if self._push_client:
            try:
                stop_result = self._push_client.stop()
                if hasattr(stop_result, "__await__"):
                    await stop_result
                _LOGGER.debug("FCM push client stopped")
            except Exception:
                _LOGGER.exception("Error stopping FCM push client")
            self._push_client = None
