"""Tests for binary sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.ajax_cobranded.api.models import Device
from custom_components.ajax_cobranded.binary_sensor import (
    _DEVICE_TYPE_SENSORS,
    BINARY_SENSOR_TYPES,
    AjaxBinarySensor,
    AjaxConnectivitySensor,
    AjaxProblemSensor,
)
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

    def test_monitoring_active_type_exists(self) -> None:
        assert "monitoring_active" in BINARY_SENSOR_TYPES

    def test_gsm_connected_type_exists(self) -> None:
        assert "gsm_connected" in BINARY_SENSOR_TYPES

    def test_lid_opened_type_exists(self) -> None:
        assert "lid_opened" in BINARY_SENSOR_TYPES

    def test_external_contact_broken_type_exists(self) -> None:
        assert "external_contact_broken" in BINARY_SENSOR_TYPES

    def test_case_drilling_type_exists(self) -> None:
        assert "case_drilling" in BINARY_SENSOR_TYPES

    def test_anti_masking_type_exists(self) -> None:
        assert "anti_masking" in BINARY_SENSOR_TYPES

    def test_malfunction_type_exists(self) -> None:
        assert "malfunction" in BINARY_SENSOR_TYPES

    def test_interference_type_exists(self) -> None:
        assert "interference" in BINARY_SENSOR_TYPES

    def test_relay_stuck_type_exists(self) -> None:
        assert "relay_stuck" in BINARY_SENSOR_TYPES

    def test_always_active_type_exists(self) -> None:
        assert "always_active" in BINARY_SENSOR_TYPES


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

    def test_hub_device_has_no_via_device(self) -> None:
        from custom_components.ajax_cobranded.api.models import Device
        from custom_components.ajax_cobranded.const import DeviceState

        hub_device = Device(
            id="hub-1",
            hub_id="hub-1",
            name="Hub",
            device_type="hub_two_4g",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={"monitoring_active": True},
            battery=None,
        )
        coordinator = MagicMock()
        coordinator.devices = {"hub-1": hub_device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="hub-1", status_key="monitoring_active"
        )
        assert sensor._attr_device_info is not None
        assert "via_device" not in sensor._attr_device_info

    def test_non_hub_device_has_via_device(self) -> None:
        device = self._make_device({})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="door_opened"
        )
        assert sensor._attr_device_info is not None
        assert sensor._attr_device_info.get("via_device") == ("ajax_cobranded", "hub-1")

    def test_monitoring_sensor_has_translation_key(self) -> None:
        from custom_components.ajax_cobranded.api.models import Device
        from custom_components.ajax_cobranded.const import DeviceState

        hub_device = Device(
            id="hub-1",
            hub_id="hub-1",
            name="Hub",
            device_type="hub_two_4g",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=None,
        )
        coordinator = MagicMock()
        coordinator.devices = {"hub-1": hub_device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="hub-1", status_key="monitoring_active"
        )
        assert sensor._attr_translation_key == "monitoring"

    def test_motion_sensor_extra_attributes_with_timestamp(self) -> None:
        device = self._make_device({"motion_detected": True, "motion_detected_at": 1700000000})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="motion_detected"
        )
        attrs = sensor.extra_state_attributes
        assert attrs.get("detected_at") == 1700000000

    def test_motion_sensor_extra_attributes_without_timestamp(self) -> None:
        device = self._make_device({"motion_detected": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(
            coordinator=coordinator, device_id="dev-1", status_key="motion_detected"
        )
        attrs = sensor.extra_state_attributes
        assert attrs == {}

    def test_non_motion_sensor_no_extra_attributes(self) -> None:
        device = self._make_device({"tamper": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxBinarySensor(coordinator=coordinator, device_id="dev-1", status_key="tamper")
        assert sensor.extra_state_attributes == {}


class TestDeviceTypeSensors:
    def test_glass_protect_s_in_device_types(self) -> None:
        assert "glass_protect_s" in _DEVICE_TYPE_SENSORS

    def test_glass_protect_fibra_in_device_types(self) -> None:
        assert "glass_protect_fibra" in _DEVICE_TYPE_SENSORS

    def test_combi_protect_s_in_device_types(self) -> None:
        assert "combi_protect_s" in _DEVICE_TYPE_SENSORS

    def test_combi_protect_fibra_in_device_types(self) -> None:
        assert "combi_protect_fibra" in _DEVICE_TYPE_SENSORS

    def test_home_siren_in_device_types(self) -> None:
        assert "home_siren" in _DEVICE_TYPE_SENSORS

    def test_street_siren_in_device_types(self) -> None:
        assert "street_siren" in _DEVICE_TYPE_SENSORS

    def test_rex_in_device_types(self) -> None:
        assert "rex" in _DEVICE_TYPE_SENSORS

    def test_rex_2_in_device_types(self) -> None:
        assert "rex_2" in _DEVICE_TYPE_SENSORS

    def test_fire_protect_plus_has_co(self) -> None:
        assert "co_detected" in _DEVICE_TYPE_SENSORS["fire_protect_plus"]

    def test_leaks_protect_has_leak(self) -> None:
        assert "leak_detected" in _DEVICE_TYPE_SENSORS["leaks_protect"]

    def test_door_protect_s_in_device_types(self) -> None:
        assert "door_protect_s" in _DEVICE_TYPE_SENSORS

    def test_door_protect_g3_in_device_types(self) -> None:
        assert "door_protect_g3" in _DEVICE_TYPE_SENSORS

    def test_motion_cam_fibra_in_device_types(self) -> None:
        assert "motion_cam_fibra" in _DEVICE_TYPE_SENSORS


class TestAjaxConnectivitySensor:
    def _make_device(self, state: DeviceState = DeviceState.ONLINE) -> Device:
        return Device(
            id="dev-1",
            hub_id="hub-1",
            name="Front Door",
            device_type="door_protect",
            room_id=None,
            group_id=None,
            state=state,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=None,
        )

    def test_is_on_when_device_online(self) -> None:
        device = self._make_device(DeviceState.ONLINE)
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is True

    def test_is_off_when_device_offline(self) -> None:
        device = self._make_device(DeviceState.OFFLINE)
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is False

    def test_is_off_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is False

    def test_unique_id(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.unique_id == "ajax_cobranded_dev-1_connectivity"

    def test_entity_category_is_diagnostic(self) -> None:
        from homeassistant.const import EntityCategory

        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_translation_key(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_translation_key == "connectivity"

    def test_device_info_set(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_device_info is not None
        assert ("ajax_cobranded", "dev-1") in sensor._attr_device_info["identifiers"]

    def test_hub_device_no_via_device(self) -> None:
        hub_device = Device(
            id="hub-1",
            hub_id="hub-1",
            name="Hub",
            device_type="hub_two_4g",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=None,
        )
        coordinator = MagicMock()
        coordinator.devices = {"hub-1": hub_device}
        sensor = AjaxConnectivitySensor(coordinator=coordinator, device_id="hub-1")
        assert "via_device" not in sensor._attr_device_info


class TestAjaxProblemSensor:
    def _make_device(self, malfunctions: int = 0) -> Device:
        return Device(
            id="dev-1",
            hub_id="hub-1",
            name="Front Door",
            device_type="door_protect",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=malfunctions,
            bypassed=False,
            statuses={},
            battery=None,
        )

    def test_is_off_when_no_malfunctions(self) -> None:
        device = self._make_device(malfunctions=0)
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is False

    def test_is_on_when_malfunctions(self) -> None:
        device = self._make_device(malfunctions=2)
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is True

    def test_is_off_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.is_on is False

    def test_unique_id(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.unique_id == "ajax_cobranded_dev-1_problem"

    def test_entity_category_is_diagnostic(self) -> None:
        from homeassistant.const import EntityCategory

        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_translation_key(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_translation_key == "problem"

    def test_extra_attributes_with_malfunctions(self) -> None:
        device = self._make_device(malfunctions=3)
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        attrs = sensor.extra_state_attributes
        assert attrs == {"malfunctions_count": 3}

    def test_extra_attributes_empty_when_device_missing(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor.extra_state_attributes == {}

    def test_device_info_set(self) -> None:
        device = self._make_device()
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}
        sensor = AjaxProblemSensor(coordinator=coordinator, device_id="dev-1")
        assert sensor._attr_device_info is not None
        assert ("ajax_cobranded", "dev-1") in sensor._attr_device_info["identifiers"]
