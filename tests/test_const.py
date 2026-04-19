"""Tests for const.py — STATUS_MAP and PILOT_MAP."""
from custom_components.eveus_chargers.const import STATUS_MAP, PILOT_MAP


class TestStatusMap:
    def test_known_states(self):
        assert STATUS_MAP[0] == "no_data"
        assert STATUS_MAP[1] == "ready"
        assert STATUS_MAP[2] == "waiting"
        assert STATUS_MAP[3] == "charging"
        assert STATUS_MAP[7] == "leakage"
        assert STATUS_MAP[8] == "no_ground"
        assert STATUS_MAP[9] == "overtemperature_system"
        assert STATUS_MAP[10] == "overtemperature_plug"
        assert STATUS_MAP[11] == "overtemperature_relay"
        assert STATUS_MAP[12] == "overcurrent"
        assert STATUS_MAP[13] == "overvoltage"
        assert STATUS_MAP[14] == "undervoltage"
        assert STATUS_MAP[15] == "limited_by_time"
        assert STATUS_MAP[16] == "limited_by_energy"
        assert STATUS_MAP[17] == "limited_by_cost"
        assert STATUS_MAP[18] == "limited_by_schedule_1"
        assert STATUS_MAP[19] == "limited_by_schedule_2"
        assert STATUS_MAP[20] == "disabled_by_user"
        assert STATUS_MAP[21] == "relay_error"
        assert STATUS_MAP[22] == "disabled_by_adaptive"

    def test_unused_codes_not_present(self):
        for code in [4, 5, 6]:
            assert code not in STATUS_MAP

    def test_unknown_code_fallback(self):
        assert STATUS_MAP.get(99, "unknown") == "unknown"

    def test_total_entries(self):
        assert len(STATUS_MAP) == 20


class TestPilotMap:
    def test_connected_states(self):
        for code in [2, 3, 5]:
            assert PILOT_MAP[code] == "connected"

    def test_disconnected_state(self):
        assert PILOT_MAP[1] == "disconnected"

    def test_unknown_states(self):
        for code in [0, 4, 6]:
            assert PILOT_MAP[code] == "unknown"

    def test_undefined_code_fallback(self):
        assert PILOT_MAP.get(99, "disconnected") == "disconnected"
