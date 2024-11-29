from homeassistant import config_entries
import voluptuous as vol
from .api import SmartHubAPI
from .const import DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

import logging
_LOGGER = logging.getLogger(__name__)

class SmartHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartHub."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate credentials by attempting to get a token
                api = SmartHubAPI(
                    email=user_input["email"],
                    password=user_input["password"],
                    account_id=user_input["account_id"],
                    location_id=user_input["location_id"],
                    host=user_input["host"],
                )
                await self.hass.async_add_executor_job(api.get_token)

                # Debug log for successful connection
                _LOGGER.debug("Successfully validated credentials in config_flow.")

                # Create an entry with the user-provided data
                return self.async_create_entry(title="SmartHub", data=user_input)

            except Exception:
                _LOGGER.error("Error validating credentials in config_flow.")
                errors["base"] = "cannot_connect"

        # Show the form again if validation failed
        schema = vol.Schema(
            {
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Required("account_id"): str,
                vol.Required("location_id"): str,
                vol.Required("host"): str,
                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): int,  # Poll interval in minutes
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

