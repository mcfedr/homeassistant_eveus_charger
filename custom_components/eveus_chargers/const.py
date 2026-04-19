DOMAIN = "eveus_chargers"
DEFAULT_SCAN_INTERVAL = 30
TITLE = "Eveus Chargers"

# Firmware-confirmed state codes (from device JS scriptUA.js array index)
STATUS_MAP = {
    0: "no_data",
    1: "ready",
    2: "waiting",
    3: "charging",
    7: "leakage",
    8: "no_ground",
    9: "overtemperature_system",
    10: "overtemperature_plug",
    11: "overtemperature_relay",
    12: "overcurrent",
    13: "overvoltage",
    14: "undervoltage",
    15: "limited_by_time",
    16: "limited_by_energy",
    17: "limited_by_cost",
    18: "limited_by_schedule_1",
    19: "limited_by_schedule_2",
    20: "disabled_by_user",
    21: "relay_error",
    22: "disabled_by_adaptive",
}

# Firmware-confirmed pilot signal mapping (from device JS switch statement)
PILOT_MAP = {
    0: "unknown",
    1: "disconnected",
    2: "connected",
    3: "connected",
    4: "unknown",
    5: "connected",
    6: "unknown",
}
