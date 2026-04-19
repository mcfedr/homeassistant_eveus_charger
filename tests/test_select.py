"""Tests for select.py — timezone option parsing."""
from custom_components.eveus_chargers.select import TimeZoneSelect, TIMEZONE_OPTIONS


def _make(mock_coordinator, mock_config_entry):
    select = object.__new__(TimeZoneSelect)
    select.coordinator = mock_coordinator
    select.config_entry = mock_config_entry
    return select


class TestTimeZoneCurrentOption:
    def test_integer_timezone(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": 3}
        assert _make(mock_coordinator, mock_config_entry).current_option == "3"

    def test_negative_timezone(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": -5}
        assert _make(mock_coordinator, mock_config_entry).current_option == "-5"

    def test_zero_timezone(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": 0}
        assert _make(mock_coordinator, mock_config_entry).current_option == "0"

    def test_float_timezone_rounded(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": "3.0"}
        assert _make(mock_coordinator, mock_config_entry).current_option == "3"

    def test_string_timezone(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": "2"}
        assert _make(mock_coordinator, mock_config_entry).current_option == "2"

    def test_invalid_value_returns_none(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": "invalid"}
        assert _make(mock_coordinator, mock_config_entry).current_option is None

    def test_out_of_range_returns_none(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"timeZone": 99}
        assert _make(mock_coordinator, mock_config_entry).current_option is None

    def test_missing_defaults_to_zero(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {}
        assert _make(mock_coordinator, mock_config_entry).current_option == "0"
