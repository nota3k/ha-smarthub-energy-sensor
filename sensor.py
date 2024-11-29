from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from datetime import timedelta
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    poll_interval = data["poll_interval"]

    # Create a coordinator to manage polling
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SmartHub Energy",
        update_method=api.get_energy_data,
        update_interval=timedelta(minutes=poll_interval),
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Create and add the sensor
    sensors = [SmartHubEnergySensor(coordinator)]
    async_add_entities(sensors)


class SmartHubEnergySensor(CoordinatorEntity, Entity):
    """Representation of the SmartHub Energy sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "SmartHub Energy Sensor"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("current_energy_usage")

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "state_class": "total",
            "unit_of_measurement": "kWh",
            "device_class": "energy",
            "icon": "mdi:power-plug",
        }
