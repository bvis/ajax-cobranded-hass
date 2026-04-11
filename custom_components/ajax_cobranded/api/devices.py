"""Devices API: streaming, parsing, and commands."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from custom_components.ajax_cobranded.api.models import BatteryInfo, Device, DeviceCommand
from custom_components.ajax_cobranded.const import DeviceState

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

_STREAM_LIGHT_DEVICES = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".stream_light_devices.StreamLightDevicesService/execute"
)
_DEVICE_ON = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_device_on.DeviceCommandDeviceOnService/execute"
)
_DEVICE_OFF = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_device_off.DeviceCommandDeviceOffService/execute"
)
_DEVICE_BRIGHTNESS = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_brightness.DeviceCommandBrightnessService/execute"
)

_STATE_MAP: dict[int, DeviceState] = {
    0: DeviceState.ONLINE,
    1: DeviceState.LOCKED,
    2: DeviceState.SUSPENDED,
    3: DeviceState.UNKNOWN,
    4: DeviceState.UNKNOWN,
    5: DeviceState.ADDING,
    6: DeviceState.ADDING,
    7: DeviceState.BATTERY_SAVING,
    8: DeviceState.NOT_MIGRATED,
    9: DeviceState.OFFLINE,
    10: DeviceState.UPDATING,
    11: DeviceState.WALK_TEST,
}


class DevicesApi:
    """API operations for devices."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    @staticmethod
    def _parse_device_state(states: Any) -> DeviceState:  # noqa: ANN401
        if not states:
            return DeviceState.ONLINE
        priority = {
            DeviceState.OFFLINE: 100,
            DeviceState.LOCKED: 90,
            DeviceState.SUSPENDED: 80,
            DeviceState.UPDATING: 70,
            DeviceState.BATTERY_SAVING: 60,
            DeviceState.WALK_TEST: 50,
            DeviceState.ADDING: 40,
            DeviceState.NOT_MIGRATED: 30,
            DeviceState.UNKNOWN: 20,
            DeviceState.ONLINE: 0,
        }
        worst = DeviceState.ONLINE
        for s in states:
            val = s if isinstance(s, int) else int(s)
            mapped = _STATE_MAP.get(val, DeviceState.UNKNOWN)
            if priority.get(mapped, 0) > priority.get(worst, 0):
                worst = mapped
        return worst

    @staticmethod
    def _parse_battery(statuses: Any) -> BatteryInfo | None:  # noqa: ANN401
        for status in statuses:
            which = status.WhichOneof("status") if hasattr(status, "WhichOneof") else None
            if which == "battery":
                return BatteryInfo(
                    level=status.battery.charge_level_percentage,
                    is_low=status.battery.battery_state not in (0, 1),  # 0=UNSPECIFIED, 1=OK
                )
        return None

    @staticmethod
    def _parse_statuses(statuses: Any) -> dict[str, Any]:  # noqa: ANN401
        result: dict[str, Any] = {}
        for status in statuses:
            which = status.WhichOneof("status") if hasattr(status, "WhichOneof") else None
            if which is None:
                continue
            if which == "door_opened":
                result["door_opened"] = True
            elif which == "motion_detected":
                result["motion_detected"] = True
            elif which == "smoke_detected":
                result["smoke_detected"] = True
            elif which == "co_level_detected":
                result["co_detected"] = True
            elif which == "high_temperature_detected":
                result["high_temperature"] = True
            elif which == "leak_detected":
                result["leak_detected"] = True
            elif which == "tamper":
                result["tamper"] = True
            elif which == "temperature":
                result["temperature"] = status.temperature.value
            elif which == "life_quality":
                lq = status.life_quality
                if hasattr(lq, "actual_temperature"):
                    result["temperature"] = lq.actual_temperature
                if hasattr(lq, "actual_humidity"):
                    result["humidity"] = lq.actual_humidity
                if hasattr(lq, "actual_co2"):
                    result["co2"] = lq.actual_co2
            elif which == "signal_strength":
                result["signal_strength"] = int(status.signal_strength.device_signal_level)
        return result

    @staticmethod
    def parse_device(proto_light_device: Any) -> Device | None:  # noqa: ANN401
        device_kind = proto_light_device.WhichOneof("device")
        if device_kind != "hub_device":
            _LOGGER.debug("Skipping non-hub device type: %s", device_kind)
            return None

        hub_dev = proto_light_device.hub_device
        common = hub_dev.common_device
        profile = common.profile

        device_type = common.object_type.WhichOneof("type") or "unknown"

        return Device(
            id=profile.id,
            hub_id=common.hub_id,
            name=profile.name,
            device_type=device_type,
            room_id=profile.room_id if profile.room_id else None,
            group_id=profile.group_id if profile.group_id else None,
            state=DevicesApi._parse_device_state(profile.states),
            malfunctions=profile.malfunctions,
            bypassed=profile.bypassed,
            statuses=DevicesApi._parse_statuses(profile.statuses),
            battery=DevicesApi._parse_battery(profile.statuses),
        )

    async def get_devices_snapshot(self, space_id: str) -> list[Device]:
        """Get initial snapshot of all devices in a space."""
        proto_path = str(Path(__file__).parent.parent / "proto")
        if proto_path not in sys.path:
            sys.path.append(proto_path)

        from v3.mobilegwsvc.service.stream_light_devices import (  # noqa: PLC0415
            endpoint_pb2_grpc,
            request_pb2,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = endpoint_pb2_grpc.StreamLightDevicesServiceStub(channel)

        request = request_pb2.StreamLightDevicesRequest(space_id=space_id)
        stream = stub.execute(request, metadata=metadata, timeout=30)

        devices: list[Device] = []
        async for msg in stream:
            if msg.HasField("success"):
                which = msg.success.WhichOneof("success")
                if which == "snapshot":
                    for light_device in msg.success.snapshot.light_devices:
                        device = self.parse_device(light_device)
                        if device is not None:
                            devices.append(device)
                    break  # Got snapshot, stop
            elif msg.HasField("failure"):
                _LOGGER.error("Device stream failed: %s", msg.failure)
                break

        return devices

    async def send_command(self, command: DeviceCommand) -> None:
        if command.action == "on":
            _LOGGER.debug("Sending ON command to %s", command.device_id)
        elif command.action == "off":
            _LOGGER.debug("Sending OFF command to %s", command.device_id)
        elif command.action == "brightness":
            _LOGGER.debug("Sending BRIGHTNESS %s to %s", command.brightness, command.device_id)

    async def capture_photo(self, hub_id: str, device_id: str, device_type: str) -> str | None:
        """Capture a photo on demand and return the image URL."""
        proto_path = str(Path(__file__).parent.parent / "proto")
        if proto_path not in sys.path:
            sys.path.append(proto_path)

        from systems.ajax.api.ecosystem.v2.hubsvc.commonmodels import (  # noqa: PLC0415
            object_type_pb2,
        )
        from v3.mobilegwsvc.service.capture_photo_on_demand_for_detection_area import (  # noqa: PLC0415
            endpoint_pb2_grpc as capture_grpc,
        )
        from v3.mobilegwsvc.service.capture_photo_on_demand_for_detection_area import (
            request_pb2 as capture_req_pb2,
        )
        from v3.mobilegwsvc.service.stream_detection_area_test import (  # noqa: PLC0415
            endpoint_pb2_grpc as stream_grpc,
        )
        from v3.mobilegwsvc.service.stream_detection_area_test import (
            request_pb2 as stream_req_pb2,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()

        # Build ObjectType with the correct device type oneof field
        obj_type = object_type_pb2.ObjectType()
        try:
            getattr(obj_type, device_type).SetInParent()
        except AttributeError:
            _LOGGER.error("Unknown device type for photo capture: %s", device_type)
            return None

        # Start streaming first to not miss the READY event
        stream_stub = stream_grpc.StreamDetectionAreaTestServiceStub(channel)
        stream = stream_stub.execute(
            stream_req_pb2.StreamDetectionAreaTestRequest(hub_id=hub_id, device_id=device_id),
            metadata=metadata,
            timeout=30,
        )

        # Trigger capture
        capture_stub = capture_grpc.CapturePhotoOnDemandForDetectionAreaServiceStub(channel)
        capture_resp = await capture_stub.execute(
            capture_req_pb2.CapturePhotoOnDemandForDetectionAreaRequest(
                hub_id=hub_id,
                device_id=device_id,
                object_type=obj_type,
            ),
            metadata=metadata,
            timeout=15,
        )

        if capture_resp.HasField("failure"):
            _LOGGER.error("Photo capture failed: %s", capture_resp.failure)
            return None

        # Wait for READY state in the stream
        async for msg in stream:
            if msg.HasField("success"):
                which = msg.success.WhichOneof("success")
                if which == "snapshot":
                    area = msg.success.snapshot.detection_area
                elif which == "update":
                    area = msg.success.update.detection_area
                else:
                    continue

                state_val = int(area.state)
                if state_val == 2:  # STATE_READY
                    if area.HasField("photo_info"):
                        return str(area.photo_info.url)
                    break
                elif state_val == 3:  # STATE_FAILED
                    _LOGGER.error("Photo capture failed on device")
                    break
            elif msg.HasField("failure"):
                _LOGGER.error("Photo stream error: %s", msg.failure)
                break

        return None
