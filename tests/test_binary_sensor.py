"""Tests for binary_sensor.py — ground status."""
from custom_components.eveus_chargers.binary_sensor import EveusGroundSensor


def _make(mock_coordinator, mock_config_entry):
    sensor = object.__new__(EveusGroundSensor)
    sensor.coordinator = mock_coordinator
    sensor.config_entry = mock_config_entry
    return sensor


class TestEveusGroundSensor:
    def test_ground_connected(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"ground": 1}
        assert _make(mock_coordinator, mock_config_entry).is_on is True

    def test_ground_not_connected(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"ground": 0}
        assert _make(mock_coordinator, mock_config_entry).is_on is False

    def test_ground_missing_defaults_false(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        assert _make(mock_coordinator, mock_config_entry).is_on is False

    def test_ground_truthy(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"ground": 2}
        assert _make(mock_coordinator, mock_config_entry).is_on is True
