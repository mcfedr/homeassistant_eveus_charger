import logging
import asyncio
from datetime import timedelta
from homeassistant.util import slugify
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EveusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str, entry: ConfigEntry):
        update_rate = entry.options.get("update_rate", 10)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} Coordinator",
            update_interval=timedelta(seconds=update_rate),
        )
        self.host = host

        self.device_name = entry.options.get(
            "device_name",
            entry.data.get("device_name", "Eveus Pro")
        )
        self.device_name_slug = slugify(self.device_name)
        self._mac: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        identifier = self._mac or self.config_entry.entry_id
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=self.device_name,
            manufacturer="Eveus",
            model="Energy Star Pro",
            sw_version=self.data.get("fwVersion") if self.data else None,
        )

    async def _async_update_data(self):
        try:
            async with asyncio.timeout(5):
                session = async_get_clientsession(self.hass)

                # Step 1: POST /init (timer/config data — non-critical)
                init_url = f"http://{self.host}/init"
                init_data = {}
                try:
                    async with session.post(init_url) as resp_init:
                        if resp_init.status == 200 and "application/json" in resp_init.headers.get("Content-Type", ""):
                            init_data = await resp_init.json()
                            if not self._mac:
                                self._mac = init_data.get("ESP_MAC")
                        else:
                            _LOGGER.warning("EveusCoordinator → /init → not JSON (%s)", resp_init.headers.get("Content-Type"))
                except Exception as err:
                    _LOGGER.warning("EveusCoordinator → /init request error: %s", repr(err))

                # Step 2: POST /main (real-time state — critical)
                main_url = f"http://{self.host}/main"
                try:
                    async with session.post(main_url, json={"getState": True}) as resp_main:
                        if resp_main.status == 200 and "application/json" in resp_main.headers.get("Content-Type", ""):
                            main_data = await resp_main.json()
                        else:
                            raise UpdateFailed(f"/main returned non-JSON response: {resp_main.headers.get('Content-Type')}")
                except UpdateFailed:
                    raise
                except Exception as err:
                    raise UpdateFailed(f"Error fetching /main: {err}") from err

                return {**init_data, **main_data}

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
