# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for local control of **Energy Star Pro** and **Eveus Pro** EV charging stations via their built-in HTTP JSON API. Domain: `eveus_chargers`. No cloud dependency — fully local polling.

## Development

There is no build system, test suite, or CI/CD. The integration is pure Python with no external PyPI dependencies (only standard HA libraries: `aiohttp`, `voluptuous`, `homeassistant`).

**To test changes:** Copy `custom_components/eveus_chargers/` into a Home Assistant instance's `config/custom_components/` directory and restart HA (or reload the integration).

**Installation via HACS:** Add `https://github.com/mcfedr/homeassistant_eveus_charger` as a custom repository (type: Integration).

## Architecture

All code lives in `custom_components/eveus_chargers/`.

**Data flow:** ConfigFlow → EVSECoordinator → Entity Platforms → HA UI

### Coordinator (`coordinator.py`)
Central data fetcher extending `DataUpdateCoordinator`. Uses `async_get_clientsession` for HTTP. Each update cycle makes two HTTP POST requests to the charging station:
- `POST /init` — timer/scheduling data (timeZone, startTime, stopTime, isAlarm)
- `POST /main` with `{"getState": True}` — real-time state (status, currents, voltages, temperatures, energy)

Responses are merged into `coordinator.data`. Update interval is configurable (1–60s, default 10s). Provides a centralized `device_info` property used by all entities.

### Device API Endpoints
- `POST /pageEvent` — send control commands (header: `pageEvent: <key>`, body: `key=value`)
- `POST /timer` — manage scheduling (body: `isAlarm=<bool>&startTime=HH:MM&stopTime=HH:MM&timeZone=<int>`)

### Entity Platforms (6)
- **sensor.py** — 15 base + 4 three-phase sensors (status as ENUM with 22 states, currents, voltages, power, temperatures, energy, session time, battery voltage, car connected via pilot signal, ground status)
- **switch.py** — 7 switches: EVSESwitch (groundCtrl, restrictedMode), EVSEScheduleSwitch (timer via `/timer`), EVSESimpleSwitch (oneCharge, aiMode, evseEnabled inverted, suspendLimits)
- **number.py** — currentSet (device-reported min–max range), aiVoltage (180–240V)
- **button.py** — SyncTimeButton (timestamp + timezone), ChargeNowButton (multi-step sequence)
- **select.py** — TimeZoneSelect (writes to `/timer`), UpdateRateSelect (updates config_entry.options, triggers reload)
- **time.py** — Uses TextEntity + CoordinatorEntity for HH:MM formatted startTime/stopTime

### Key Patterns
- **Entity naming:** All entities use `has_entity_name=True` with translation keys driving display names via `strings.json`
- **Unique IDs:** `{translation_key}_{entry_id}`
- **Device name slugification:** `coordinator.device_name_slug` used across all entity IDs
- **Status mapping:** Integer status codes → translation keys via `STATUS_MAP` in `const.py` (22 firmware-confirmed states from device JS)
- **Pilot mapping:** Integer pilot signal → connected/disconnected/unknown via `PILOT_MAP` in `const.py`
- **Value scaling:** Device returns values in native units (A, kWh, W) — no division needed
- **Schedule writes:** Always send the full scheduling payload when updating any single timer field
- **Device info:** Centralized in `coordinator.device_info` — all entities reference it

## Translations

Two languages: English (`en.json`) and Ukrainian (`uk.json`), plus `strings.json` (base keys). All entity names, states, config flow labels, and errors are translated.

## Device Support

Supports 1-phase and 3-phase configurations (selected during setup). Three-phase mode adds 4 additional current/voltage sensors. Device type stored in `config_entry.options["device_type"]`.
