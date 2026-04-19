import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SWITCH_DEFINITIONS = [
    ("groundCtrl", "eveus_chargers_control_pe"),
    ("restrictedMode", "eveus_chargers_restricted_mode"),
]

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        EveusSwitch(coordinator, entry, key, trans_key)
        for key, trans_key in SWITCH_DEFINITIONS
    ]

    entities.append(EveusScheduleSwitch(coordinator, entry))
    entities.append(EveusSimpleSwitch(coordinator, entry, "oneCharge", "eveus_chargers_one_charge"))
    entities.append(EveusSimpleSwitch(coordinator, entry, "aiMode", "eveus_chargers_adaptive_mode", state_key="aiStatus"))
    entities.append(EveusSimpleSwitch(coordinator, entry, "evseEnabled", "eveus_chargers_charger_enabled", inverted=True))
    entities.append(EveusSimpleSwitch(coordinator, entry, "suspendLimits", "eveus_chargers_suspend_limits", enabled_default=False))

    async_add_entities(entities)

class EveusSwitch(SwitchEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, key, translation_key):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._host = coordinator.host
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{translation_key}_{config_entry.entry_id}"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def is_on(self):
        if self._key == "restrictedMode":
            return float(self.coordinator.data.get("currentSet", 32)) <= 16
        return bool(self.coordinator.data.get(self._key))

    async def async_turn_on(self):
        if self._key == "restrictedMode":
            await self._set_current_if_needed(12, only_if_high=True)
        else:
            await self._send_event(True)

    async def async_turn_off(self):
        if self._key == "restrictedMode":
            await self._set_current_if_needed(16, only_if_low=True)
        else:
            await self._send_event(False)

    async def _send_event(self, state: bool):
        payload = f"{self._key}={'1' if state else '0'}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "pageEvent": self._key
        }
        session = async_get_clientsession(self.coordinator.hass)
        try:
            await session.post(f"http://{self._host}/pageEvent", data=payload, headers=headers)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("switch.py → request error %s → %s", self._key, repr(err))

    async def _set_current_if_needed(self, target, only_if_high=False, only_if_low=False):
        current = float(self.coordinator.data.get("currentSet", 32))
        if (only_if_high and current > target) or (only_if_low and current <= target):
            payload = f"currentSet={target}"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "pageEvent": "currentSet"
            }
            session = async_get_clientsession(self.coordinator.hass)
            await session.post(f"http://{self._host}/pageEvent", data=payload, headers=headers)
            await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return self.coordinator.device_info

class EveusScheduleSwitch(SwitchEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._host = coordinator.host
        self._attr_translation_key = "eveus_chargers_schedule"
        self._attr_unique_id = f"schedule_{config_entry.entry_id}"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def is_on(self):
        value = self.coordinator.data.get("isAlarm")
        return str(value).lower() in ["true", "1"]

    async def async_turn_on(self):
        await self._send(True)

    async def async_turn_off(self):
        await self._send(False)

    async def _send(self, state: bool):
        data = self.coordinator.data
        if not data:
            _LOGGER.warning("switch.py → coordinator.data empty, schedule not updated")
            return

        payload = (
            f"isAlarm={'true' if state else 'false'}&"
            f"startTime={data.get('startTime')}&"
            f"stopTime={data.get('stopTime')}&"
            f"timeZone={data.get('timeZone')}"
        )
        session = async_get_clientsession(self.coordinator.hass)
        try:
            await session.post(f"http://{self._host}/timer", data=payload, headers={
                "Content-Type": "application/x-www-form-urlencoded"
            })
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("switch.py → schedule update error → %s", repr(err))

    @property
    def device_info(self):
        return self.coordinator.device_info

class EveusSimpleSwitch(SwitchEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, key, translation_key, *, state_key=None, inverted=False, enabled_default=True):
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._host = coordinator.host
        self._key = key
        self._state_key = state_key or key
        self._inverted = inverted
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{translation_key}_{config_entry.entry_id}"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def is_on(self):
        val = self.coordinator.data.get(self._state_key)
        raw_on = str(val).lower() in ["true", "1"]
        return not raw_on if self._inverted else raw_on

    async def async_turn_on(self):
        await self._send(True)

    async def async_turn_off(self):
        await self._send(False)

    async def _send(self, state: bool):
        # For inverted switches, flip the value sent to the device
        device_state = not state if self._inverted else state
        payload = f"{self._key}={'1' if device_state else '0'}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "pageEvent": self._key
        }
        session = async_get_clientsession(self.coordinator.hass)
        try:
            await session.post(f"http://{self._host}/pageEvent", data=payload, headers=headers)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("switch.py → request error %s → %s", self._key, repr(err))

    @property
    def device_info(self):
        return self.coordinator.device_info
