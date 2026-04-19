import logging
from datetime import datetime, timezone
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, STATUS_MAP, PILOT_MAP

_LOGGER = logging.getLogger(__name__)

# (key, translation_key, unit, state_class, device_class, enabled_default)
SENSOR_DEFINITIONS = [
    ("state", "eveus_chargers_status", None, None, SensorDeviceClass.ENUM, True),
    ("curMeas1", "eveus_chargers_current_phase_1", "A", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("voltMeas1", "eveus_chargers_voltage_phase_1", "V", SensorStateClass.MEASUREMENT, SensorDeviceClass.VOLTAGE, True),
    ("powerMeas", "eveus_chargers_power", "W", SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER, True),
    ("temperature1", "eveus_chargers_temperature_box", "°C", SensorStateClass.MEASUREMENT, SensorDeviceClass.TEMPERATURE, True),
    ("temperature2", "eveus_chargers_temperature_socket", "°C", SensorStateClass.MEASUREMENT, SensorDeviceClass.TEMPERATURE, True),
    ("leakValue", "eveus_chargers_leakage", "mA", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("sessionEnergy", "eveus_chargers_session_energy", "kWh", SensorStateClass.TOTAL_INCREASING, SensorDeviceClass.ENERGY, True),
    ("sessionTime", "eveus_chargers_session_time", "s", SensorStateClass.MEASUREMENT, SensorDeviceClass.DURATION, True),
    ("totalEnergy", "eveus_chargers_total_energy", "kWh", SensorStateClass.TOTAL_INCREASING, SensorDeviceClass.ENERGY, True),
    ("systemTime", "eveus_chargers_system_time", None, None, SensorDeviceClass.TIMESTAMP, False),
    ("vBat", "eveus_chargers_battery_voltage", "V", SensorStateClass.MEASUREMENT, SensorDeviceClass.VOLTAGE, False),
]

THREE_PHASE_SENSORS = [
    ("curMeas2", "eveus_chargers_current_phase_2", "A", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("curMeas3", "eveus_chargers_current_phase_3", "A", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("voltMeas2", "eveus_chargers_voltage_phase_2", "V", SensorStateClass.MEASUREMENT, SensorDeviceClass.VOLTAGE, True),
    ("voltMeas3", "eveus_chargers_voltage_phase_3", "V", SensorStateClass.MEASUREMENT, SensorDeviceClass.VOLTAGE, True),
]

STATUS_OPTIONS = sorted(set(STATUS_MAP.values())) + ["unknown"]
PILOT_OPTIONS = sorted(set(PILOT_MAP.values()))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    device_type = entry.options.get("device_type", entry.data.get("device_type", "1_phase"))

    entities = [
        EveusSensor(coordinator, entry, key, trans_key, unit, state_class, device_class, enabled_default)
        for key, trans_key, unit, state_class, device_class, enabled_default in SENSOR_DEFINITIONS
    ]

    if device_type == "3_phase":
        entities += [
            EveusSensor(coordinator, entry, key, trans_key, unit, state_class, device_class, enabled_default)
            for key, trans_key, unit, state_class, device_class, enabled_default in THREE_PHASE_SENSORS
        ]

    entities.append(EveusPilotSensor(coordinator, entry))
    async_add_entities(entities)


class EveusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, key, translation_key, unit, state_class, device_class, enabled_default=True):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_device_class = device_class
        self._attr_entity_registry_enabled_default = enabled_default

        if key == "state":
            self._attr_options = STATUS_OPTIONS

        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"
        self._attr_unique_id = f"{translation_key}_{config_entry.entry_id}"

    @property
    def suggested_display_precision(self) -> int | None:
        if self._key == "vBat":
            return 2
        return None

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        try:
            if self._key == "curMeas1":
                return round(float(value), 2)
            if self._key in ["sessionEnergy", "totalEnergy"]:
                return round(float(value), 3)
            if self._key == "powerMeas":
                return round(float(value), 1)
            if self._key == "vBat":
                return round(float(value), 2)
            if self._key == "sessionTime":
                return int(float(value))
            if self._key == "systemTime":
                return datetime.fromtimestamp(int(float(value)), tz=timezone.utc)
            if self._key == "state":
                return STATUS_MAP.get(value, "unknown")
            return value
        except Exception as err:
            _LOGGER.warning("sensor.py → error processing %s: %s", self._key, repr(err))
            return None

    @property
    def device_info(self):
        return self.coordinator.device_info


class EveusPilotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_translation_key = "eveus_chargers_car_connected"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = PILOT_OPTIONS

        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"
        self._attr_unique_id = f"car_connected_{config_entry.entry_id}"

    @property
    def native_value(self):
        value = self.coordinator.data.get("pilot")
        if value is None:
            return None
        return PILOT_MAP.get(int(value), "disconnected")

    @property
    def device_info(self):
        return self.coordinator.device_info
