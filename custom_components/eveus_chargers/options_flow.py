from homeassistant import config_entries
import voluptuous as vol

DEVICE_TYPES = {
    "1_phase": "1_phase",
    "3_phase": "3_phase"
}


class EveusOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options
        data = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("host", default=current.get("host", data.get("host", ""))): str,
                vol.Optional("username", default=current.get("username", data.get("username", ""))): str,
                vol.Optional("password", default=current.get("password", data.get("password", ""))): str,
                vol.Required("device_type",
                             default=current.get("device_type", data.get("device_type", "1_phase"))): vol.In(
                    DEVICE_TYPES),
            }),
        )
