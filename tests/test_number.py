"""Tests for number.py — dynamic min/max values."""
from custom_components.eveus_chargers.number import EveusNumber, NUMBER_DEFINITIONS


def _make_number(mock_coordinator, mock_config_entry, definition):
    """Create a number entity bypassing HA base init."""
    num = object.__new__(EveusNumber)
    num.coordinator = mock_coordinator
    num.config_entry = mock_config_entry
    num._host = mock_coordinator.host
    num._key = definition["key"]
    num._config = definition
    return num


class TestCurrentSetMinMax:
    def _get_definition(self):
        return [d for d in NUMBER_DEFINITIONS if d["key"] == "currentSet"][0]

    def test_min_from_device_data(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"minCurrent": 7}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_min_value == 7.0

    def test_min_fallback_to_config(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_min_value == 6.0  # config default

    def test_max_from_device_data(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"curDesign": 40}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_max_value == 40.0

    def test_max_fallback_to_config(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_max_value == 32.0  # config default


class TestAiVoltageMinMax:
    def _get_definition(self):
        return [d for d in NUMBER_DEFINITIONS if d["key"] == "aiVoltage"][0]

    def test_static_min(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_min_value == 180

    def test_static_max(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        num = _make_number(mock_coordinator, mock_config_entry, self._get_definition())
        assert num.native_max_value == 240


class TestNativeValue:
    def test_returns_float(self, mock_coordinator, mock_config_entry):
        definition = [d for d in NUMBER_DEFINITIONS if d["key"] == "currentSet"][0]
        mock_coordinator.data = {"currentSet": 16}
        num = _make_number(mock_coordinator, mock_config_entry, definition)
        assert num.native_value == 16.0

    def test_none_when_missing(self, mock_coordinator, mock_config_entry):
        definition = [d for d in NUMBER_DEFINITIONS if d["key"] == "currentSet"][0]
        mock_coordinator.data = {}
        num = _make_number(mock_coordinator, mock_config_entry, definition)
        assert num.native_value is None
