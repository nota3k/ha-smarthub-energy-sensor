"""Config flow for SmartHub integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .api import SmartHubAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartHub."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Generate a unique ID from input that should uniquely identify this account/host
            # This is crucial for Home Assistant to manage the integration instance.
            unique_id = (
                f"{user_input['email']}_{user_input['host']}_{user_input['account_id']}"
            )

            # Set the unique ID for this config entry.
            # If an entry with this unique ID already exists, abort the flow.
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()  # Check if already configured

            try:
                # Validate credentials by attempting to get a token
                api = SmartHubAPI(
                    email=user_input["email"],
                    password=user_input["password"],
                    account_id=user_input["account_id"],
                    location_id=user_input["location_id"],
                    host=user_input["host"],
                )

                await api.get_token()

                # Create an entry with the user-provided data
                return self.async_create_entry(title="SmartHub", data=user_input)

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error validating credentials in config_flow")
                errors["base"] = "cannot_connect"

        # Show the form again if validation failed or it's the first time
        schema = vol.Schema(
            {
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Required("account_id"): str,
                vol.Required("location_id"): str,
                vol.Required("host"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
