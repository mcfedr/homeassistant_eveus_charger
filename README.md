# Eveus Chargers

Home Assistant integration for local control of **Energy Star Pro** and **Eveus Pro** EV charging stations via their built-in web interface (JSON API).

![Logo](custom_components/eveus_chargers/brand/icon.png)

---

## Features

- Real-time sensors: power, voltage, current, temperature, energy, battery voltage
- Charging status with all 22 device states (ready, charging, waiting, error conditions, limits, etc.)
- Car connection detection (pilot signal)
- Control charging current (full range from device min to max)
- Start/stop charging, enable/disable charger
- Scheduled charging with start/stop times
- Adaptive mode and voltage threshold control
- Suspend limits toggle
- Time synchronization
- Configurable polling rate (1–60 seconds)
- Support for 1-phase and 3-phase configurations
- Full local operation — no cloud dependency
- UI configuration via Config Flow
- English and Ukrainian translations

---

## Installation

### Option 1: via HACS (recommended)

1. Open HACS -> "Integrations" -> "Custom repositories"
2. Add repository:
   ```
   https://github.com/V-Plum/evse_energy_star
   ```
3. Select category: `Integration`
4. Install the integration
5. Restart Home Assistant

### Option 2: Manual

1. Download ZIP archive or clone the repository
2. Copy the `eveus_chargers` folder to:
   ```
   config/custom_components/eveus_chargers
   ```
3. Restart Home Assistant

---

## Configuration

1. Go to `Settings` -> `Devices & Services` -> `Add Integration`
2. Search for "Eveus Chargers"
3. Enter:
   - Device name
   - Charging station IP address
   - Username (optional)
   - Password (optional)
   - Device type (single-phase or three-phase)

---

## Entities

### Sensors

| Entity | Description | Unit |
|---|---|---|
| Charging Status | Device state (22 states including charging, ready, error conditions, limits) | enum |
| Set Current | Currently configured charging current | A |
| Phase 1 Current | Measured current (phase 1) | A |
| Phase 1 Voltage | Measured voltage (phase 1) | V |
| Power | Active power | W |
| Box Temperature | Internal temperature | °C |
| Socket Temperature | Plug/socket temperature | °C |
| Leakage | Leakage current | mA |
| Session Energy | Energy consumed in current session | kWh |
| Session Duration | Duration of current session | HH:MM:SS |
| Total Energy | Lifetime energy counter | kWh |
| Car Connected | Pilot signal — car connection status | enum |
| System Time | Device clock (disabled by default) | — |
| Battery Voltage | Internal battery (disabled by default) | V |
| Ground Status | Ground connection indicator (disabled by default) | — |

Three-phase devices add: Phase 2/3 Current and Phase 2/3 Voltage.

### Switches

| Entity | Description |
|---|---|
| Charger Enabled | Enable/disable charging (inverted evseEnabled) |
| Ground Control | Ground fault protection |
| 16A Mode | Restrict to 16A domestic socket mode |
| Scheduled Charging | Enable timer-based charging |
| One-Time Charge | Single charge session mode |
| Adaptive Mode | Voltage-adaptive charging |
| Suspend Limits | Temporarily disable limits (disabled by default) |

### Numbers

| Entity | Range | Description |
|---|---|---|
| Current Limit | minCurrent – curDesign (device-reported) | Charging current setpoint |
| Adaptive Voltage | 180–240 V | Undervoltage threshold for adaptive mode |

### Buttons

| Entity | Description |
|---|---|
| Sync Time | Synchronize device clock from HA |
| Start Charging | Reset limits/schedules and begin charging |

### Selects

| Entity | Description |
|---|---|
| Time Zone | Device timezone offset (-12 to +12) |
| Update Rate | Polling interval (1, 2, 5, 10, 15, 30, 60 seconds) |

### Text

| Entity | Description |
|---|---|
| Start Time | Schedule start time (HH:MM) |
| Stop Time | Schedule stop time (HH:MM) |

---

## Requirements

- Home Assistant 2023.0 or newer
- Energy Star Pro or Eveus Pro charging station with active web interface

---

## Acknowledgments

Original integration by **[@V-Plum](https://github.com/V-Plum/evse_energy_star)**.
Improvements informed by the fork by **[@d-primikirio](https://github.com/d-primikirio/eveus_hacs)**.

Pull requests, issues, and stars are welcome!

---

## License

[MIT License](LICENSE)
