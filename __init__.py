from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import SmartHubAPI
from .const import DOMAIN, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    config = entry.data

    # Initialize the API object
    api = SmartHubAPI(
        email=config["email"],
        password=config["password"],
        account_id=config["account_id"],
        location_id=config["location_id"],
        host=config["host"],
    )

    # Store the API instance in hass.data
    hass.data.setdefault(DOMAIN, {})
    
    # Get poll interval from options if available, otherwise from config data
    poll_interval = entry.options.get(CONF_POLL_INTERVAL) or config.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "poll_interval": poll_interval,
    }

    # Forward setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False

