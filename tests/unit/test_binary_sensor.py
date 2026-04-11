"""Tests for binary sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.ajax_cobranded.api.models import Device
from custom_components.ajax_cobranded.binary_sensor import BINARY_SENSOR_TYPES, AjaxBinarySensor
from custom_components.ajax_cobranded.const import DeviceState


class TestBinarySensorTypes:
    def test_door_sensor_type_exists(self) -> None:
        assert "door_opened" in BINARY_SENSOR_TYPES

    def test_motion_sensor_type_exists(self) -> None:
        assert "motion_detected" in BINARY_SENSOR_TYPES

    def test_smoke_sensor_type_exists(self) -> None:
        assert "smoke_detected" in BINARY_SENSOR_TYPES

    def test_leak_sensor_type_exists(self) -> None:
        assert "leak_detected" in BINARY_SENSOR_TYPES

    def test_tamper_sensor_type_exists(self) -> None:
        assert "tamper" in BINARY_SENSOR_TYPES

    def test_co_sensor_type_exists(self) -> None:
        assert "co_detected" in BINARY_SENSOR_TYPES

    def test_high_temperature_type_exists(self) -> None:
        assert "high_temperature" in BINARY_SENSOR_TYPES


class TestAjaxBinarySensor:
    def _make_device(self, statuses: dict) -> Device:
        return Device(
            id="dev-1",
            hub_id="hub-1",
            name="Front Door",
            device_type="door_protect",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses=statuses,
            battery=None,
        )

    def test_is_on_true(self) -> None:
        device = self._make_device({"door_opened": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.is_on is True

    def test_is_on_false_when_key_absent(self) -> None:
        device = self._make_device({})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.is_on is False

    def test_is_on_false_when_no_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.is_on is False

    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": self._make_device({})}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.unique_id == "ajax_cobranded_dev-1_door_opened"

    def test_device_info_with_device(self) -> None:
        device = self._make_device({})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor._attr_device_info is not None
        assert ("ajax_cobranded", "dev-1") in sensor._attr_device_info["identifiers"]

    def test_device_info_without_device(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert not hasattr(sensor, "_attr_device_info") or sensor._attr_device_info is None

    def test_available_when_online(self) -> None:
        device = self._make_device({})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.available is True

    def test_unavailable_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor.available is False

    def test_motion_sensor(self) -> None:
        device = self._make_device({"motion_detected": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="motion_detected"
        )
        assert sensor.is_on is True

    def test_tamper_sensor(self) -> None:
        device = self._make_device({"tamper": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(coordinator=coordinator, device_id="dev-1", status_key="tamper")
        assert sensor.is_on is True
