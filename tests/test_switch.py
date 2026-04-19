"""Tests for switch.py — state logic and inverted switches."""
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.eveus_chargers.switch import EveusSwitch, EveusSimpleSwitch, EveusScheduleSwitch


def _make_switch(cls, mock_coordinator, mock_config_entry, **kwargs):
    """Create a switch instance bypassing HA base init."""
    switch = object.__new__(cls)
    switch.coordinator = mock_coordinator
    switch.config_entry = mock_config_entry
    switch._host = mock_coordinator.host
    return switch


class TestEveusSwitchIsOn:
    def test_restricted_mode_on_when_current_low(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"currentSet": 12}
        switch = _make_switch(EveusSwitch, mock_coordinator, mock_config_entry)
        switch._key = "restrictedMode"
        assert switch.is_on is True

    def test_restricted_mode_on_at_boundary(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"currentSet": 16}
        switch = _make_switch(EveusSwitch, mock_coordinator, mock_config_entry)
        switch._key = "restrictedMode"
        assert switch.is_on is True

    def test_restricted_mode_off_when_current_high(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"currentSet": 32}
        switch = _make_switch(EveusSwitch, mock_coordinator, mock_config_entry)
        switch._key = "restrictedMode"
        assert switch.is_on is False

    def test_normal_switch_on(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"groundCtrl": 1}
        switch = _make_switch(EveusSwitch, mock_coordinator, mock_config_entry)
        switch._key = "groundCtrl"
        assert switch.is_on is True

    def test_normal_switch_off(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"groundCtrl": 0}
        switch = _make_switch(EveusSwitch, mock_coordinator, mock_config_entry)
        switch._key = "groundCtrl"
        assert switch.is_on is False


class TestEveusSimpleSwitchIsOn:
    def test_normal_on(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"oneCharge": "1"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "oneCharge"
        switch._state_key = "oneCharge"
        switch._inverted = False
        assert switch.is_on is True

    def test_normal_off(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"oneCharge": "0"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "oneCharge"
        switch._state_key = "oneCharge"
        switch._inverted = False
        assert switch.is_on is False

    def test_inverted_on_when_device_off(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"evseEnabled": "0"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "evseEnabled"
        switch._state_key = "evseEnabled"
        switch._inverted = True
        assert switch.is_on is True

    def test_inverted_off_when_device_on(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"evseEnabled": "1"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "evseEnabled"
        switch._state_key = "evseEnabled"
        switch._inverted = True
        assert switch.is_on is False

    def test_state_key_reads_different_field(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"aiStatus": "1", "aiMode": "0"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "aiMode"
        switch._state_key = "aiStatus"
        switch._inverted = False
        assert switch.is_on is True

    def test_true_string(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"oneCharge": "true"}
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "oneCharge"
        switch._state_key = "oneCharge"
        switch._inverted = False
        assert switch.is_on is True


class TestEveusSimpleSwitchSend:
    @patch("custom_components.eveus_chargers.switch.async_get_clientsession")
    async def test_inverted_turn_on_sends_zero(self, mock_session_fn, mock_coordinator, mock_config_entry):
        session = AsyncMock()
        mock_session_fn.return_value = session
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "evseEnabled"
        switch._state_key = "evseEnabled"
        switch._inverted = True
        await switch._send(True)  # turn on
        call_kwargs = session.post.call_args
        assert "evseEnabled=0" in str(call_kwargs)

    @patch("custom_components.eveus_chargers.switch.async_get_clientsession")
    async def test_inverted_turn_off_sends_one(self, mock_session_fn, mock_coordinator, mock_config_entry):
        session = AsyncMock()
        mock_session_fn.return_value = session
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "evseEnabled"
        switch._state_key = "evseEnabled"
        switch._inverted = True
        await switch._send(False)  # turn off
        call_kwargs = session.post.call_args
        assert "evseEnabled=1" in str(call_kwargs)

    @patch("custom_components.eveus_chargers.switch.async_get_clientsession")
    async def test_normal_turn_on_sends_one(self, mock_session_fn, mock_coordinator, mock_config_entry):
        session = AsyncMock()
        mock_session_fn.return_value = session
        switch = _make_switch(EveusSimpleSwitch, mock_coordinator, mock_config_entry)
        switch._key = "oneCharge"
        switch._state_key = "oneCharge"
        switch._inverted = False
        await switch._send(True)
        call_kwargs = session.post.call_args
        assert "oneCharge=1" in str(call_kwargs)


class TestEveusScheduleSwitchIsOn:
    def _make(self, mock_coordinator, mock_config_entry):
        switch = object.__new__(EveusScheduleSwitch)
        switch.coordinator = mock_coordinator
        switch.config_entry = mock_config_entry
        switch._host = mock_coordinator.host
        return switch

    def test_true_string(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"isAlarm": "true"}
        assert self._make(mock_coordinator, mock_config_entry).is_on is True

    def test_one_string(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"isAlarm": "1"}
        assert self._make(mock_coordinator, mock_config_entry).is_on is True

    def test_false_string(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"isAlarm": "false"}
        assert self._make(mock_coordinator, mock_config_entry).is_on is False

    def test_zero_string(self, mock_coordinator, mock_config_entry):
        mock_coordinator.data = {"isAlarm": "0"}
        assert self._make(mock_coordinator, mock_config_entry).is_on is False
