"""Shared fixtures for Eveus Chargers tests."""
import sys
from types import ModuleType
from unittest.mock import MagicMock, AsyncMock

# Stub out homeassistant modules so we can import integration code without HA installed
HA_MODULES = [
    "homeassistant",
    "homeassistant.core",
    "homeassistant.config_entries",
    "homeassistant.helpers",
    "homeassistant.helpers.typing",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.device_registry",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.switch",
    "homeassistant.components.number",
    "homeassistant.components.button",
    "homeassistant.components.select",
    "homeassistant.components.text",
    "homeassistant.components.binary_sensor",
    "homeassistant.helpers.selector",
    "homeassistant.helpers.translation",
    "homeassistant.util",
    "homeassistant.util.dt",
    "voluptuous",
]

for mod_name in HA_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = ModuleType(mod_name)

# Provide the classes/constants that our code imports
ha_sensor = sys.modules["homeassistant.components.sensor"]
ha_sensor.SensorEntity = type("SensorEntity", (), {})
ha_sensor.SensorStateClass = type("SensorStateClass", (), {
    "MEASUREMENT": "measurement",
    "TOTAL_INCREASING": "total_increasing",
    "TOTAL": "total",
})
ha_sensor.SensorDeviceClass = type("SensorDeviceClass", (), {
    "ENUM": "enum",
    "CURRENT": "current",
    "VOLTAGE": "voltage",
    "POWER": "power",
    "TEMPERATURE": "temperature",
    "ENERGY": "energy",
    "DURATION": "duration",
    "TIMESTAMP": "timestamp",
})

ha_switch = sys.modules["homeassistant.components.switch"]
ha_switch.SwitchEntity = type("SwitchEntity", (), {})

ha_number = sys.modules["homeassistant.components.number"]
ha_number.NumberEntity = type("NumberEntity", (), {})
ha_number.NumberDeviceClass = type("NumberDeviceClass", (), {
    "CURRENT": "current",
    "VOLTAGE": "voltage",
})

ha_button = sys.modules["homeassistant.components.button"]
ha_button.ButtonEntity = type("ButtonEntity", (), {})

ha_select = sys.modules["homeassistant.components.select"]
ha_select.SelectEntity = type("SelectEntity", (), {"__init__": lambda self: None})
ha_select.SelectEntityDescription = lambda **kwargs: MagicMock(**kwargs)

ha_text = sys.modules["homeassistant.components.text"]
ha_text.TextEntity = type("TextEntity", (), {})
ha_text.TextEntityDescription = lambda **kwargs: MagicMock(**kwargs)

ha_binary = sys.modules["homeassistant.components.binary_sensor"]
ha_binary.BinarySensorEntity = type("BinarySensorEntity", (), {})
ha_binary.BinarySensorDeviceClass = type("BinarySensorDeviceClass", (), {
    "SAFETY": "safety",
})

# CoordinatorEntity stub
ha_coordinator = sys.modules["homeassistant.helpers.update_coordinator"]
ha_coordinator.CoordinatorEntity = type("CoordinatorEntity", (), {
    "__init__": lambda self, coordinator: setattr(self, "coordinator", coordinator),
})
ha_coordinator.DataUpdateCoordinator = type("DataUpdateCoordinator", (), {
    "__init__": lambda self, *a, **kw: None,
})


class _UpdateFailed(Exception):
    pass


ha_coordinator.UpdateFailed = _UpdateFailed

ha_device_reg = sys.modules["homeassistant.helpers.device_registry"]
ha_device_reg.DeviceInfo = dict

ha_aiohttp = sys.modules["homeassistant.helpers.aiohttp_client"]
ha_aiohttp.async_get_clientsession = MagicMock()

ha_config = sys.modules["homeassistant.config_entries"]
ha_config.ConfigEntry = type("ConfigEntry", (), {})
ha_config.ConfigFlow = type("ConfigFlow", (), {})
ha_config.OptionsFlow = type("OptionsFlow", (), {})
ha_config.CONN_CLASS_LOCAL_POLL = "local_poll"

ha_core = sys.modules["homeassistant.core"]
ha_core.HomeAssistant = type("HomeAssistant", (), {})

ha_entity_platform = sys.modules["homeassistant.helpers.entity_platform"]
ha_entity_platform.AddEntitiesCallback = None

ha_selector = sys.modules["homeassistant.helpers.selector"]
ha_selector.SelectSelector = MagicMock()
ha_selector.SelectSelectorConfig = MagicMock()

ha_translation = sys.modules["homeassistant.helpers.translation"]
ha_translation.async_get_translations = AsyncMock(return_value={})

ha_util = sys.modules["homeassistant.util"]
ha_util.slugify = lambda s: s.lower().replace(" ", "_")

sys.modules["voluptuous"] = MagicMock()

import pytest


@pytest.fixture
def mock_config_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = {
        "host": "10.2.0.135",
        "device_name": "Eveus Pro",
        "device_type": "1_phase",
        "username": "",
        "password": "",
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_coordinator(mock_config_entry):
    coordinator = MagicMock()
    coordinator.host = "10.2.0.135"
    coordinator.device_name = "Eveus Pro"
    coordinator.device_name_slug = "eveus_pro"
    coordinator.config_entry = mock_config_entry
    coordinator.last_update_success = True
    coordinator.hass = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.device_info = {
        "identifiers": {("eveus_chargers", "test_entry_123")},
        "name": "Eveus Pro",
        "manufacturer": "Eveus",
        "model": "Energy Star Pro",
    }
    coordinator.data = {}
    return coordinator


SAMPLE_MAIN_DATA = {
    "state": 1,
    "pilot": 1,
    "currentSet": 16,
    "curDesign": 40,
    "minCurrent": 7,
    "curMeas1": 12.345,
    "voltMeas1": 239.9449158,
    "powerMeas": 2834.567,
    "temperature1": 19,
    "temperature2": 9,
    "leakValue": 0,
    "vBat": 0.72026366,
    "sessionEnergy": 35.79663467,
    "sessionTime": 21341,
    "totalEnergy": 4216.09668,
    "systemTime": 1776592439,
    "evseEnabled": 0,
    "aiStatus": 0,
    "ground": 1,
    "isAlarm": "false",
    "STA_IP_Addres": "10.2.0.135",
}

SAMPLE_INIT_DATA = {
    "curDesign": 40,
    "minCurrent": 7,
    "ESP_MAC": "C8:F0:9E:CB:02:D0",
    "ssidNameAP": "AP_EVSE_02D0",
    "timeZone": 3,
    "startTime": "23:00",
    "stopTime": "07:00",
}
