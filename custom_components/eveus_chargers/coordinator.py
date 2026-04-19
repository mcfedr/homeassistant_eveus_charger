import logging
import async_timeout
from datetime import timedelta
from homeassistant.util import slugify
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
            name=f"{DOMAIN} Coordinator",
            update_interval=timedelta(seconds=update_rate),
        )
        self.hass = hass
        self.host = host
        self.entry = entry

        self.device_name = entry.options.get(
            "device_name",
            entry.data.get("device_name", "Eveus Pro")
        )

        self.device_name_slug = slugify(self.device_name)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.device_name,
            "manufacturer": "Eveus",
            "model": "Energy Star Pro",
            "sw_version": self.data.get("fwVersion") if self.data else None,
        }

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(5):
                session = async_get_clientsession(self.hass)

                # Step 1: POST /init
                init_url = f"http://{self.host}/init"
                _LOGGER.debug("EveusCoordinator → POST /init: %s", init_url)

                init_data = {}
                try:
                    async with session.post(init_url) as resp_init:
                        if resp_init.status == 200 and "application/json" in resp_init.headers.get("Content-Type", ""):
                            init_data = await resp_init.json()
                        else:
                            _LOGGER.warning("EveusCoordinator → /init → not JSON (%s)", resp_init.headers.get("Content-Type"))
                except Exception as err:
                    _LOGGER.error("EveusCoordinator → /init request error: %s", repr(err))

                # Step 2: POST /main
                main_url = f"http://{self.host}/main"
                _LOGGER.debug("EveusCoordinator → POST /main: %s", main_url)

                main_data = {}
                try:
                    async with session.post(main_url, json={"getState": True}) as resp_main:
                        if resp_main.status == 200 and "application/json" in resp_main.headers.get("Content-Type", ""):
                            main_data = await resp_main.json()
                        else:
                            _LOGGER.warning("EveusCoordinator → /main → not JSON (%s)", resp_main.headers.get("Content-Type"))
                except Exception as err:
                    _LOGGER.error("EveusCoordinator → /main request error: %s", repr(err))

                combined = {**init_data, **main_data}
                return combined

        except Exception as err:
            _LOGGER.error("EveusCoordinator → general error: %s", repr(err))
            return {}
