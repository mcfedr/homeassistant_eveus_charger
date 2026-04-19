import logging
from datetime import datetime
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
    ("currentSet", "eveus_chargers_current_set", "A", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("curMeas1", "eveus_chargers_current_phase_1", "A", SensorStateClass.MEASUREMENT, SensorDeviceClass.CURRENT, True),
    ("voltMeas1", "eveus_chargers_voltage_phase_1", "V", SensorStateClass.MEASUREMENT, SensorDeviceClass.VOLTAGE, True),
    ("powerMeas", "eveus_chargers_power", "W", SensorStateClass.MEASUREMENT, SensorDeviceClass.POWER, True),
    ("temperature1", "eveus_chargers_temperature_box", "°C", SensorStateClass.MEASUREMENT, SensorDeviceClass.TEMPERATURE, True),
    ("temperature2", "eveus_chargers_temperature_socket", "°C", SensorStateClass.MEASUREMENT, SensorDeviceClass.TEMPERATURE, True),
    ("leakValue", "eveus_chargers_leakage", "mA", SensorStateClass.MEASUREMENT, None, True),
    ("sessionEnergy", "eveus_chargers_session_energy", "kWh", SensorStateClass.TOTAL_INCREASING, SensorDeviceClass.ENERGY, True),
    ("sessionTime", "eveus_chargers_session_time", None, None, None, True),
    ("totalEnergy", "eveus_chargers_total_energy", "kWh", SensorStateClass.TOTAL_INCREASING, SensorDeviceClass.ENERGY, True),
    ("systemTime", "eveus_chargers_system_time", None, None, None, False),
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

    entities.append(EveusGroundStatus(coordinator, entry))
    entities.append(EveusPilotSensor(coordinator, entry))
    async_add_entities(entities)


class EveusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry, key, translation_key, unit, state_class, device_class, enabled_default=True):
        super().__init__(coordinator)
        self.coordinator = coordinator
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
    def available(self) -> bool:
        return self.coordinator.last_update_success

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
                total_sec = int(float(value))
                h = total_sec // 3600
                m = (total_sec % 3600) // 60
                s = total_sec % 60
                return f"{h:02}:{m:02}:{s:02}"
            if self._key == "state":
                return STATUS_MAP.get(value, "unknown")
            return value
        except Exception as err:
            _LOGGER.warning("sensor.py → error processing %s: %s", self._key, repr(err))
            return str(value)

    def _handle_coordinator_update(self):
        new_value = self.coordinator.data.get(self._key)
        if self._key == "systemTime":
            try:
                old_str = str(self._attr_native_value)
                new_str = str(new_value)
                fmt = "%H:%M:%S"
                old_dt = datetime.strptime(old_str, fmt)
                new_dt = datetime.strptime(new_str, fmt)
                if abs((new_dt - old_dt).total_seconds()) <= 2:
                    return
            except Exception as err:
                _LOGGER.debug("sensor.py → systemTime comparison: %s", repr(err))

        self._attr_native_value = new_value
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.coordinator.device_info


class EveusGroundStatus(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_translation_key = "eveus_chargers_ground_status"
        self._attr_entity_registry_enabled_default = False

        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"
        self._attr_unique_id = f"ground_status_{config_entry.entry_id}"

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        return "✅" if bool(self.coordinator.data.get("ground", 0)) else "❌"

    @property
    def icon(self):
        return "mdi:checkbox-marked-circle" if self.native_value == "✅" else "mdi:close-circle-outline"

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.coordinator.device_info


class EveusPilotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, config_entry: ConfigEntry):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._attr_translation_key = "eveus_chargers_car_connected"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = PILOT_OPTIONS

        self._attr_has_entity_name = True
        self._attr_suggested_object_id = f"{self.coordinator.device_name_slug}_{self._attr_translation_key}"
        self._attr_unique_id = f"car_connected_{config_entry.entry_id}"

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def native_value(self):
        value = self.coordinator.data.get("pilot")
        if value is None:
            return None
        return PILOT_MAP.get(int(value), "disconnected")

    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.coordinator.device_info
