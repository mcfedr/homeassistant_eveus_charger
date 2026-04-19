import logging
from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TEXT_DESCRIPTIONS = [
    TextEntityDescription(
        key="startTime",
        translation_key="eveus_chargers_start_time",
        icon="mdi:clock-time-four-outline"
    ),
    TextEntityDescription(
        key="stopTime",
        translation_key="eveus_chargers_stop_time",
        icon="mdi:clock-time-four-outline"
    ),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        EveusTimeField(coordinator, entry, description)
        for description in TEXT_DESCRIPTIONS
    ]
    async_add_entities(entities)

class EveusTimeField(CoordinatorEntity, TextEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, description: TextEntityDescription):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.entity_description = description
        self._key = description.key

        self._attr_translation_key = description.translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{description.translation_key}_{config_entry.entry_id}"
        self._attr_native_value = None
        self._attr_native_min = 4
        self._attr_native_max = 5
        self._attr_mode = "text"
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{description.translation_key}"

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)
        return str(value) if value is not None else None

    async def async_set_value(self, value: str):
        data = self.coordinator.data
        updated = {
            "startTime": data.get("startTime"),
            "stopTime": data.get("stopTime"),
            "timeZone": data.get("timeZone"),
            "isAlarm": str(data.get("isAlarm")).lower(),
        }
        updated[self._key] = value

        payload = (
            f"isAlarm={updated['isAlarm']}&"
            f"startTime={updated['startTime']}&"
            f"stopTime={updated['stopTime']}&"
            f"timeZone={updated['timeZone']}"
        )

        try:
            session = async_get_clientsession(self.coordinator.hass)
            await session.post(
                f"http://{self.coordinator.host}/timer",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("time.py → error writing %s = %s → %s", self._key, value, err)

    @property
    def device_info(self):
        return self.coordinator.device_info
