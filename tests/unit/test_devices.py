"""Tests for devices API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import pytest

from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.models import Device, DeviceCommand
from custom_components.ajax_cobranded.const import DeviceState


class TestParseDevice:
    def test_parse_hub_device(self) -> None:
        proto_device = MagicMock()
        proto_device.hub_device.common_device.profile.id = "dev-1"
        proto_device.hub_device.common_device.profile.name = "Front Door"
        proto_device.hub_device.common_device.profile.room_id = "room-1"
        proto_device.hub_device.common_device.profile.group_id = ""
        proto_device.hub_device.common_device.profile.malfunctions = 0
        proto_device.hub_device.common_device.profile.bypassed = False
        proto_device.hub_device.common_device.profile.device_marketing_id = "DoorProtect"
        proto_device.hub_device.common_device.profile.states = []
        proto_device.hub_device.common_device.profile.statuses = []
        proto_device.hub_device.common_device.hub_id = "hub-1"
        proto_device.hub_device.common_device.object_type.WhichOneof.return_value = "door_protect"
        proto_device.WhichOneof.return_value = "hub_device"

        device = DevicesApi.parse_device(proto_device)
        assert isinstance(device, Device)
        assert device.id == "dev-1"
        assert device.name == "Front Door"
        assert device.hub_id == "hub-1"
        assert device.device_type == "door_protect"
        assert device.room_id == "room-1"
        assert device.state == DeviceState.ONLINE

    def test_parse_offline_device(self) -> None:
        proto_device = MagicMock()
        proto_device.hub_device.common_device.profile.id = "dev-2"
        proto_device.hub_device.common_device.profile.name = "Motion"
        proto_device.hub_device.common_device.profile.room_id = ""
        proto_device.hub_device.common_device.profile.group_id = ""
        proto_device.hub_device.common_device.profile.malfunctions = 0
        proto_device.hub_device.common_device.profile.bypassed = False
        proto_device.hub_device.common_device.profile.device_marketing_id = "MotionProtect"
        proto_device.hub_device.common_device.profile.states = [9]  # OFFLINE
        proto_device.hub_device.common_device.profile.statuses = []
        proto_device.hub_device.common_device.hub_id = "hub-1"
        proto_device.hub_device.common_device.object_type.WhichOneof.return_value = "motion_protect"
        proto_device.WhichOneof.return_value = "hub_device"

        device = DevicesApi.parse_device(proto_device)
        assert device is not None
        assert device.state == DeviceState.OFFLINE

    def test_parse_non_hub_device_returns_none(self) -> None:
        proto_device = MagicMock()
        proto_device.WhichOneof.return_value = "video_edge"
        result = DevicesApi.parse_device(proto_device)
        assert result is None


class TestDeviceStateParser:
    def test_empty_states_returns_online(self) -> None:
        result = DevicesApi._parse_device_state([])
        assert result == DeviceState.ONLINE

    def test_none_states_returns_online(self) -> None:
        result = DevicesApi._parse_device_state(None)
        assert result == DeviceState.ONLINE

    def test_offline_state(self) -> None:
        result = DevicesApi._parse_device_state([9])
        assert result == DeviceState.OFFLINE

    def test_worst_state_wins(self) -> None:
        # Mix of battery_saving (60) and offline (100) -> offline
        result = DevicesApi._parse_device_state([7, 9])
        assert result == DeviceState.OFFLINE

    def test_unknown_state_code(self) -> None:
        result = DevicesApi._parse_device_state([99])
        assert result == DeviceState.UNKNOWN


class TestBatteryParser:
    def test_parse_battery_found(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "battery"
        status.battery.charge_level_percentage = 75
        status.battery.battery_state = 1  # OK

        result = DevicesApi._parse_battery([status])
        assert result is not None
        assert result.level == 75
        assert result.is_low is False

    def test_parse_battery_low(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "battery"
        status.battery.charge_level_percentage = 10
        status.battery.battery_state = 2  # LOW

        result = DevicesApi._parse_battery([status])
        assert result is not None
        assert result.is_low is True

    def test_parse_battery_not_found(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "door_opened"
        result = DevicesApi._parse_battery([status])
        assert result is None

    def test_parse_battery_empty(self) -> None:
        result = DevicesApi._parse_battery([])
        assert result is None


class TestStatusParser:
    def test_door_opened_status(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "door_opened"
        result = DevicesApi._parse_statuses([status])
        assert result.get("door_opened") is True

    def test_motion_detected_status(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "motion_detected"
        result = DevicesApi._parse_statuses([status])
        assert result.get("motion_detected") is True

    def test_smoke_detected(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "smoke_detected"
        result = DevicesApi._parse_statuses([status])
        assert result.get("smoke_detected") is True

    def test_co_detected(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "co_level_detected"
        result = DevicesApi._parse_statuses([status])
        assert result.get("co_detected") is True

    def test_temperature_status(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "temperature"
        status.temperature.value = 22.5
        result = DevicesApi._parse_statuses([status])
        assert result.get("temperature") == 22.5

    def test_leak_detected(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "leak_detected"
        result = DevicesApi._parse_statuses([status])
        assert result.get("leak_detected") is True

    def test_tamper_status(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "tamper"
        result = DevicesApi._parse_statuses([status])
        assert result.get("tamper") is True

    def test_high_temperature(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "high_temperature_detected"
        result = DevicesApi._parse_statuses([status])
        assert result.get("high_temperature") is True

    def test_signal_strength(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "signal_strength"
        status.signal_strength.device_signal_level = 3
        result = DevicesApi._parse_statuses([status])
        assert result.get("signal_strength") == 3

    def test_life_quality_status(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = "life_quality"
        lq = MagicMock()
        lq.actual_temperature = 21.0
        lq.actual_humidity = 55.0
        lq.actual_co2 = 400
        status.life_quality = lq
        result = DevicesApi._parse_statuses([status])
        assert result.get("temperature") == 21.0
        assert result.get("humidity") == 55.0
        assert result.get("co2") == 400

    def test_none_which_oneof_skipped(self) -> None:
        status = MagicMock()
        status.WhichOneof.return_value = None
        result = DevicesApi._parse_statuses([status])
        assert result == {}

    def test_no_whichoneof_attr(self) -> None:
        # status without WhichOneof method
        class SimpleStatus:
            pass

        result = DevicesApi._parse_statuses([SimpleStatus()])
        assert result == {}


class TestDevicesApiInit:
    def test_init(self) -> None:
        client = MagicMock()
        api = DevicesApi(client)
        assert api._client is client


class TestSendCommand:
    @pytest.mark.asyncio
    async def test_send_command_on(self) -> None:
        client = MagicMock()
        api = DevicesApi(client)
        cmd = DeviceCommand.on(hub_id="h1", device_id="d1", device_type="relay", channels=[1])
        # Should not raise
        await api.send_command(cmd)

    @pytest.mark.asyncio
    async def test_send_command_off(self) -> None:
        client = MagicMock()
        api = DevicesApi(client)
        cmd = DeviceCommand.off(hub_id="h1", device_id="d1", device_type="relay", channels=[1])
        await api.send_command(cmd)

    @pytest.mark.asyncio
    async def test_send_command_brightness(self) -> None:
        client = MagicMock()
        api = DevicesApi(client)
        cmd = DeviceCommand.set_brightness(
            hub_id="h1",
            device_id="d1",
            device_type="light_switch_dimmer",
            brightness=50,
            channels=[1],
        )
        await api.send_command(cmd)


class TestGetDevicesSnapshot:
    @pytest.mark.asyncio
    async def test_get_devices_snapshot_success(self) -> None:
        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_client._get_channel.return_value = mock_channel
        mock_client._session.get_call_metadata.return_value = []

        api = DevicesApi(mock_client)

        # Build a mock device to be returned in snapshot
        mock_light_device = MagicMock()
        mock_light_device.WhichOneof.return_value = "hub_device"
        mock_light_device.hub_device.common_device.profile.id = "dev-1"
        mock_light_device.hub_device.common_device.profile.name = "Sensor"
        mock_light_device.hub_device.common_device.profile.room_id = ""
        mock_light_device.hub_device.common_device.profile.group_id = ""
        mock_light_device.hub_device.common_device.profile.malfunctions = 0
        mock_light_device.hub_device.common_device.profile.bypassed = False
        mock_light_device.hub_device.common_device.profile.states = []
        mock_light_device.hub_device.common_device.profile.statuses = []
        mock_light_device.hub_device.common_device.hub_id = "hub-1"
        mock_light_device.hub_device.common_device.object_type.WhichOneof.return_value = (
            "door_protect"
        )

        # Build the snapshot message
        mock_msg = MagicMock()
        mock_msg.HasField.side_effect = lambda field: field == "success"
        mock_msg.success.WhichOneof.return_value = "snapshot"
        mock_msg.success.snapshot.light_devices = [mock_light_device]

        # Async iterator for stream
        async def _aiter(*args: object, **kwargs: object) -> AsyncGenerator[MagicMock, None]:
            yield mock_msg

        mock_stub_instance = MagicMock()
        mock_stub_instance.execute.return_value = _aiter()
        mock_stub_class = MagicMock(return_value=mock_stub_instance)

        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(StreamLightDevicesServiceStub=mock_stub_class)

        with patch.dict(
            "sys.modules",
            {
                "v3.mobilegwsvc.service.stream_light_devices.endpoint_pb2_grpc": mock_grpc_module,
                "v3.mobilegwsvc.service.stream_light_devices.request_pb2": mock_request_pb2,
                "v3.mobilegwsvc.service.stream_light_devices": MagicMock(
                    endpoint_pb2_grpc=mock_grpc_module,
                    request_pb2=mock_request_pb2,
                ),
            },
        ):
            devices = await api.get_devices_snapshot("space-1")

        assert len(devices) == 1
        assert devices[0].id == "dev-1"

    @pytest.mark.asyncio
    async def test_get_devices_snapshot_failure_message(self) -> None:
        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_client._get_channel.return_value = mock_channel
        mock_client._session.get_call_metadata.return_value = []

        api = DevicesApi(mock_client)

        # Build a failure message
        mock_msg = MagicMock()
        mock_msg.HasField.side_effect = lambda field: field == "failure"

        async def _aiter(*args: object, **kwargs: object) -> AsyncGenerator[MagicMock, None]:
            yield mock_msg

        mock_stub_instance = MagicMock()
        mock_stub_instance.execute.return_value = _aiter()
        mock_stub_class = MagicMock(return_value=mock_stub_instance)

        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(StreamLightDevicesServiceStub=mock_stub_class)

        with patch.dict(
            "sys.modules",
            {
                "v3.mobilegwsvc.service.stream_light_devices.endpoint_pb2_grpc": mock_grpc_module,
                "v3.mobilegwsvc.service.stream_light_devices.request_pb2": mock_request_pb2,
                "v3.mobilegwsvc.service.stream_light_devices": MagicMock(
                    endpoint_pb2_grpc=mock_grpc_module,
                    request_pb2=mock_request_pb2,
                ),
            },
        ):
            devices = await api.get_devices_snapshot("space-1")

        assert devices == []

    @pytest.mark.asyncio
    async def test_get_devices_snapshot_update_message_ignored(self) -> None:
        """Success messages that are 'update' type (not snapshot) are not counted."""
        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_client._get_channel.return_value = mock_channel
        mock_client._session.get_call_metadata.return_value = []

        api = DevicesApi(mock_client)

        # First message is an 'update' (not snapshot), second is snapshot
        mock_msg_update = MagicMock()
        mock_msg_update.HasField.side_effect = lambda field: field == "success"
        mock_msg_update.success.WhichOneof.return_value = "update"

        mock_msg_snapshot = MagicMock()
        mock_msg_snapshot.HasField.side_effect = lambda field: field == "success"
        mock_msg_snapshot.success.WhichOneof.return_value = "snapshot"
        mock_msg_snapshot.success.snapshot.light_devices = []

        async def _aiter(*args: object, **kwargs: object) -> AsyncGenerator[MagicMock, None]:
            yield mock_msg_update
            yield mock_msg_snapshot

        mock_stub_instance = MagicMock()
        mock_stub_instance.execute.return_value = _aiter()
        mock_stub_class = MagicMock(return_value=mock_stub_instance)

        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(StreamLightDevicesServiceStub=mock_stub_class)

        with patch.dict(
            "sys.modules",
            {
                "v3.mobilegwsvc.service.stream_light_devices.endpoint_pb2_grpc": mock_grpc_module,
                "v3.mobilegwsvc.service.stream_light_devices.request_pb2": mock_request_pb2,
                "v3.mobilegwsvc.service.stream_light_devices": MagicMock(
                    endpoint_pb2_grpc=mock_grpc_module,
                    request_pb2=mock_request_pb2,
                ),
            },
        ):
            devices = await api.get_devices_snapshot("space-1")

        assert devices == []
