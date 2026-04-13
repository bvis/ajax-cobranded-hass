"""Tests for camera entities."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _stub_camera_module() -> None:
    """Stub out homeassistant.components.camera to avoid numpy dependency."""
    if "homeassistant.components.camera" not in sys.modules:
        camera_mod = ModuleType("homeassistant.components.camera")

        class Camera:
            """Minimal Camera stub."""

            def __init__(self) -> None:
                pass

        camera_mod.Camera = Camera  # type: ignore[attr-defined]
        sys.modules["homeassistant.components.camera"] = camera_mod


_stub_camera_module()

from custom_components.ajax_cobranded.camera import (  # noqa: E402
    CAMERA_DEVICE_TYPES,
    PHOD_DEVICE_TYPES,
    AjaxCamera,
)


class TestCameraDeviceTypes:
    def test_motion_cam_phod_is_camera(self) -> None:
        assert "motion_cam_phod" in CAMERA_DEVICE_TYPES

    def test_motion_cam_is_camera(self) -> None:
        assert "motion_cam" in CAMERA_DEVICE_TYPES

    def test_motion_cam_outdoor_is_camera(self) -> None:
        assert "motion_cam_outdoor" in CAMERA_DEVICE_TYPES

    def test_motion_cam_fibra_is_camera(self) -> None:
        assert "motion_cam_fibra" in CAMERA_DEVICE_TYPES


class TestPhodDeviceTypes:
    def test_motion_cam_phod_is_phod(self) -> None:
        assert "motion_cam_phod" in PHOD_DEVICE_TYPES

    def test_motion_cam_outdoor_phod_is_phod(self) -> None:
        assert "motion_cam_outdoor_phod" in PHOD_DEVICE_TYPES

    def test_motion_cam_fibra_base_is_phod(self) -> None:
        assert "motion_cam_fibra_base" in PHOD_DEVICE_TYPES

    def test_regular_motion_cam_is_not_phod(self) -> None:
        assert "motion_cam" not in PHOD_DEVICE_TYPES

    def test_motion_cam_outdoor_is_not_phod(self) -> None:
        assert "motion_cam_outdoor" not in PHOD_DEVICE_TYPES

    def test_phod_types_are_subset_of_camera_types(self) -> None:
        assert PHOD_DEVICE_TYPES.issubset(CAMERA_DEVICE_TYPES)


class TestAjaxCamera:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        assert cam.unique_id == "ajax_cobranded_d1_camera"

    def test_has_camera_image_method(self) -> None:
        coordinator = MagicMock()
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        assert hasattr(cam, "async_camera_image")

    def test_name_is_none(self) -> None:
        """Camera is the primary entity and adopts device name."""
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.name = "Front Camera"
        coordinator.devices = {"d1": mock_device}
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam"
        )
        assert cam._attr_name is None

    def test_device_info_with_device(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.id = "d1"
        mock_device.name = "Front Camera"
        mock_device.device_type = "motion_cam"
        mock_device.hub_id = "h1"
        coordinator.devices = {"d1": mock_device}
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam"
        )
        assert cam._attr_device_info is not None
        assert ("ajax_cobranded", "d1") in cam._attr_device_info["identifiers"]

    def test_device_info_without_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam"
        )
        assert not hasattr(cam, "_attr_device_info") or cam._attr_device_info is None

    def test_available_when_device_online(self) -> None:
        coordinator = MagicMock()
        mock_device = MagicMock()
        mock_device.is_online = True
        coordinator.devices = {"d1": mock_device}
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam"
        )
        assert cam.available is True

    def test_unavailable_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam"
        )
        assert cam.available is False

    @pytest.mark.asyncio
    async def test_async_camera_image_returns_bytes_via_media_stream(self) -> None:
        """Full success path: capture -> notification_id -> media stream -> download."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value="NOTIF123")
        coordinator.notification_listener = mock_listener
        coordinator.media_api.get_photo_url = AsyncMock(
            return_value="https://app.prod.ajax.systems/photo.jpg"
        )

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"fake_image_data")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch(
            "custom_components.ajax_cobranded.camera.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await cam.async_camera_image()

        assert result == b"fake_image_data"
        mock_listener.wait_for_notification_id.assert_called_once_with("d1", timeout=15.0)
        coordinator.media_api.get_photo_url.assert_called_once_with("NOTIF123", "h1", timeout=15.0)

    @pytest.mark.asyncio
    async def test_async_camera_image_uses_cached_url_from_button(self) -> None:
        """When button already retrieved a URL, camera uses it directly."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {
            "d1": "https://hubs-uploaded-resources.s3.amazonaws.com/photo.jpg"
        }

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"cached_url_data")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch(
            "custom_components.ajax_cobranded.camera.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await cam.async_camera_image()

        assert result == b"cached_url_data"
        # URL should be consumed (popped)
        assert "d1" not in coordinator.last_photo_urls

    @pytest.mark.asyncio
    async def test_async_camera_image_returns_none_when_capture_fails(self) -> None:
        """When capture_photo returns None, no URL wait happens and cached image returned."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value=None)
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value=None)
        coordinator.notification_listener = mock_listener

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = None

        result = await cam.async_camera_image()
        assert result is None
        mock_listener.wait_for_notification_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_camera_image_returns_cached_when_no_url(self) -> None:
        """When both notification_id and push URL fail, cached image is returned."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value=None)
        mock_listener.wait_for_photo_url = AsyncMock(return_value=None)
        coordinator.notification_listener = mock_listener

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = b"old_image"

        result = await cam.async_camera_image()
        assert result == b"old_image"

    @pytest.mark.asyncio
    async def test_async_camera_image_media_stream_no_url(self) -> None:
        """When notification_id arrives but media stream returns no URL."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value="NOTIF456")
        coordinator.notification_listener = mock_listener
        coordinator.media_api.get_photo_url = AsyncMock(return_value=None)

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = b"old_image"

        result = await cam.async_camera_image()
        assert result == b"old_image"

    @pytest.mark.asyncio
    async def test_async_camera_image_handles_http_error(self) -> None:
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value="NOTIF789")
        coordinator.notification_listener = mock_listener
        coordinator.media_api.get_photo_url = AsyncMock(
            return_value="https://app.prod.ajax.systems/photo.jpg"
        )

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = b"old_image"

        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.read = AsyncMock(return_value=b"not found")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with patch(
            "custom_components.ajax_cobranded.camera.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await cam.async_camera_image()

        # Returns old cached image since 404 didn't update it
        assert result == b"old_image"

    @pytest.mark.asyncio
    async def test_async_camera_image_handles_download_exception(self) -> None:
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        mock_listener = MagicMock()
        mock_listener.wait_for_notification_id = AsyncMock(return_value="NOTIF_EXC")
        coordinator.notification_listener = mock_listener
        coordinator.media_api.get_photo_url = AsyncMock(
            return_value="https://app.prod.ajax.systems/photo.jpg"
        )

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = b"cached"

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("network error"))

        with patch(
            "custom_components.ajax_cobranded.camera.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await cam.async_camera_image()

        # Should return cached image on exception
        assert result == b"cached"

    @pytest.mark.asyncio
    async def test_async_camera_image_no_notification_listener(self) -> None:
        """When notification_listener is None, capture returns but no URL wait."""
        coordinator = MagicMock()
        coordinator.last_photo_urls = {}
        coordinator.devices_api.capture_photo = AsyncMock(return_value="d1")
        coordinator.notification_listener = None

        cam = AjaxCamera(
            coordinator=coordinator, device_id="d1", hub_id="h1", device_type="motion_cam_phod"
        )
        cam._last_image = b"cached"

        result = await cam.async_camera_image()
        assert result == b"cached"
