import logging
from datetime import datetime
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    slug = coordinator.device_name_slug

    async_add_entities([
        SyncTimeButton(coordinator, entry, slug),
        ChargeNowButton(coordinator, entry, slug)
    ])


class SyncTimeButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, slug: str):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = "eveus_chargers_time_get"
        self._attr_unique_id = f"time_get_{config_entry.entry_id}"
        self._attr_icon = "mdi:clock-check-outline"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{slug}_{self._attr_translation_key}"

    async def async_press(self):
        try:
            raw_tz = self.coordinator.data.get("timeZone", 0)
            try:
                tz = int(float(str(raw_tz).strip()))
            except Exception:
                tz = 0
                _LOGGER.warning("button.py → invalid timeZone value: '%s'", raw_tz)

            local_ts = int(datetime.now().timestamp())
            system_time = local_ts + tz * 3600

            session = async_get_clientsession(self.coordinator.hass)
            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data=f"systemTime={system_time}",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        except Exception as err:
            _LOGGER.error("button.py → time sync error: %s", repr(err))

    @property
    def device_info(self):
        return self.coordinator.device_info


class ChargeNowButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, slug: str):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = "eveus_chargers_start_now"
        self._attr_unique_id = f"start_now_{config_entry.entry_id}"
        self._attr_icon = "mdi:battery-charging-high"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{slug}_{self._attr_translation_key}"

    async def async_press(self):
        try:
            data = self.coordinator.data
            tz_raw = data.get("timeZone", 0)
            try:
                tz = int(float(str(tz_raw).strip()))
            except Exception:
                tz = 0
                _LOGGER.warning("chargeNow → invalid timeZone value: '%s'", tz_raw)

            start = data.get("startTime", "23:00")
            stop = data.get("stopTime", "07:00")
            session = async_get_clientsession(self.coordinator.hass)

            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data="oneCharge=0",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data="evseEnabled=1",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            payload_timer = f"isAlarm=false&startTime={start}&stopTime={stop}&timeZone={tz}"
            await session.post(
                f"http://{self.coordinator.host}/timer",
                data=payload_timer,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data="timeLimit=500000",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data="energyLimit=10000",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            await session.post(
                f"http://{self.coordinator.host}/pageEvent",
                data="chargeNow=12",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        except Exception as err:
            _LOGGER.error("chargeNow → request error: %s", repr(err))

    @property
    def device_info(self):
        return self.coordinator.device_info
