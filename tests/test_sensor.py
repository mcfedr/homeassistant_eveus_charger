"""Tests for sensor.py — value transformations."""
from datetime import datetime, timezone
from custom_components.eveus_chargers.sensor import EveusSensor, EveusPilotSensor
import pytest


def _make_sensor(mock_coordinator, mock_config_entry, key, **overrides):
    """Create a sensor instance with mocked coordinator, bypassing HA base init."""
    defaults = {
        "translation_key": f"eveus_chargers_{key}",
        "unit": None,
        "state_class": None,
        "device_class": None,
        "enabled_default": True,
    }
    defaults.update(overrides)
    sensor = object.__new__(EveusSensor)
    sensor.coordinator = mock_coordinator
    sensor.config_entry = mock_config_entry
    sensor._key = key
    sensor._attr_translation_key = defaults["translation_key"]
    sensor._attr_native_unit_of_measurement = defaults["unit"]
    sensor._attr_state_class = defaults["state_class"]
    sensor._attr_device_class = defaults["device_class"]
    return sensor


class TestEveusSensorNativeValue:
    def test_curMeas1_rounds_to_2dp(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"curMeas1": 12.3456}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "curMeas1")
        assert sensor.native_value == 12.35

    def test_session_energy_rounds_to_3dp(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"sessionEnergy": 35.79663467}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "sessionEnergy")
        assert sensor.native_value == 35.797

    def test_total_energy_rounds_to_3dp(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"totalEnergy": 4216.09668}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "totalEnergy")
        assert sensor.native_value == 4216.097

    def test_power_rounds_to_1dp(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"powerMeas": 2834.567}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "powerMeas")
        assert sensor.native_value == 2834.6

    def test_vbat_rounds_to_2dp(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"vBat": 0.72026366}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "vBat")
        assert sensor.native_value == 0.72

    def test_session_time_returns_int_seconds(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"sessionTime": 21341}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "sessionTime")
        assert sensor.native_value == 21341

    def test_session_time_handles_float(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"sessionTime": 3661.5}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "sessionTime")
        assert sensor.native_value == 3661

    def test_system_time_returns_utc_datetime(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"systemTime": 1776592439}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "systemTime")
        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        assert result == datetime.fromtimestamp(1776592439, tz=timezone.utc)

    def test_state_maps_known_code(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"state": 3}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "state")
        assert sensor.native_value == "charging"

    def test_state_maps_unknown_code(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"state": 99}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "state")
        assert sensor.native_value == "unknown"

    def test_none_value_returns_none(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "curMeas1")
        assert sensor.native_value is None

    def test_passthrough_for_other_keys(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"voltMeas1": 239.9}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "voltMeas1")
        assert sensor.native_value == 239.9

    def test_error_returns_none(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"curMeas1": "not_a_number"}
        sensor = _make_sensor(mock_coordinator, mock_config_entry, "curMeas1")
        assert sensor.native_value is None


class TestEveusPilotSensor:
    def _make(self, mock_coordinator, mock_config_entry):
        sensor = object.__new__(EveusPilotSensor)
        sensor.coordinator = mock_coordinator
        sensor.config_entry = mock_config_entry
        return sensor

    def test_connected(self, mock_coordinator, mock_config_entry):
        for code in [2, 3, 5]:
            mock_coordinator.data = {"pilot": code}
            assert self._make(mock_coordinator, mock_config_entry).native_value == "connected"

    def test_disconnected(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"pilot": 1}
        assert self._make(mock_coordinator, mock_config_entry).native_value == "disconnected"

    def test_unknown(self, mock_coordinator, mock_config_entry):
        for code in [0, 4, 6]:
            mock_coordinator.data = {"pilot": code}
            assert self._make(mock_coordinator, mock_config_entry).native_value == "unknown"

    def test_undefined_code_defaults_disconnected(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"pilot": 99}
        assert self._make(mock_coordinator, mock_config_entry).native_value == "disconnected"

    def test_none_returns_none(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        assert self._make(mock_coordinator, mock_config_entry).native_value is None
