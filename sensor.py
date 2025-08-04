import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""

    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    poll_interval = data["poll_interval"]

    # Use the unique_id from the config_entry as the base for the sensor's unique_id.
    # If config_entry.unique_id is None (e.g., for older entries or failed config flow),
    # fall back to config_entry.entry_id which is guaranteed to be unique for the entry.
    base_unique_id = config_entry.unique_id
    if base_unique_id is None:
        _LOGGER.warning(
            "Config entry unique_id is None for %s. Falling back to entry_id. "
            "Consider deleting and re-adding the integration to get a proper unique_id.",
            config_entry.entry_id
        )
        base_unique_id = config_entry.entry_id # Fallback to a guaranteed unique string

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
    sensors = [
        SmartHubEnergySensor(coordinator, base_unique_id),
        SmartHubEnergyCostSensor(coordinator, base_unique_id),
        SmartHubEnergyDemandSensor(coordinator, base_unique_id),
    ]
    async_add_entities(sensors)


class SmartHubEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of the SmartHub Energy sensor."""

    def __init__(self, coordinator, base_unique_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._base_unique_id = base_unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        # You might want to make the name more dynamic based on parts of the unique ID
        # For instance, if you want to include the account ID in the name:
        # try:
        #     parts = self._base_unique_id.split('_')
        #     if len(parts) >= 3:
        #         return f"SmartHub Energy Sensor (Account: {parts[2]})"
        # except Exception:
        #     pass # Fallback to generic name if split fails
        return "SmartHub Energy Sensor"

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        # Combine the base_unique_id (from config_entry) with a sensor-specific identifier
        # This ensures the sensor itself has a unique ID within the Home Assistant instance.
        if not self._base_unique_id:
            _LOGGER.error("unique_id requested but _base_unique_id is None. This should not happen.")
            return None # Or raise an exception, though None is usually handled gracefully by HA

        return f"{self._base_unique_id}_energy_usage"

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        # Ensure that self.coordinator.data is not None before accessing it
        if self.coordinator.data is not None:
            return self.coordinator.data.get("current_energy_usage")

        return None # Return None if data is not available

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            "icon": "mdi:power-plug",
        }
        # Example: if your API provides other useful data, add it here
        # if self.coordinator.data:
        #     attrs["last_bill_date"] = self.coordinator.data.get("last_bill_date")
        #     attrs["total_billed_energy"] = self.coordinator.data.get("total_billed_energy")
        return attrs

    @property
    def device_class(self) -> str:
        """Return the device class."""
        return "energy"

    @property
    def state_class(self) -> str:
        """Return the state class."""
        return "total_increasing"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return "kWh"

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Return information about the device."""
        if not self._base_unique_id:
            _LOGGER.warning("base_unique_id is missing, cannot create device_info for sensor.")
            return None # Cannot create a device without a base identifier

        host_name = "Unknown Host" # Default if host can't be extracted
        account_id_suffix = "Unknown Account" # Default if account ID can't be extracted
        configuration_url = None

        try:
            parts = self._base_unique_id.split('_')

            # Assuming the format is email_host_account_id (3 parts)
            if len(parts) >= 2:
                host_name = parts[1] # This is the host part
                if host_name: # Ensure it's not an empty string
                    configuration_url = f"https://{host_name}/" # Or just http:// depending on your hub
            if len(parts) >= 3:
                account_id_suffix = parts[2] # This is the account_id part

        except IndexError:
            pass  # Use defaults
        except Exception as e:
            _LOGGER.warning(f"Error parsing base_unique_id '{self._base_unique_id}' for device_info: {e}")
            # Fallback for host_name and account_id_suffix if parsing fails
            host_name = "Parsing Error"
            account_id_suffix = "Parsing Error"

        return {
            "identifiers": {(DOMAIN, self._base_unique_id)},
            "name": f"{host_name} ({account_id_suffix})", # Naming the device with the account ID for clarity
            "manufacturer": "gagata",
            "model": "Energy Monitor",
            "configuration_url": configuration_url,
        }


class SmartHubEnergyCostSensor(CoordinatorEntity, SensorEntity):
    """Representation of the SmartHub Energy cost sensor."""

    def __init__(self, coordinator, base_unique_id: str):
        super().__init__(coordinator)
        self._base_unique_id = base_unique_id

    @property
    def name(self) -> str:
        return "SmartHub Energy Cost"

    @property
    def unique_id(self) -> str:
        return f"{self._base_unique_id}_energy_cost"

    @property
    def state(self) -> Optional[float]:
        if self.coordinator.data is not None:
            cost = self.coordinator.data.get("current_energy_cost")
            if cost is not None:
                return cost
        return None

    @property
    def available(self) -> bool:
        """Return True if cost data is available."""
        return (self.coordinator.data is not None and 
                self.coordinator.data.get("current_energy_cost") is not None)

    @property
    def unit_of_measurement(self) -> str:
        return "USD"  # Change to your currency if needed

    @property
    def device_class(self) -> str:
        return "monetary"

    @property
    def state_class(self) -> str:
        return "total_increasing"

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Return information about the device."""
        if not self._base_unique_id:
            return None

        try:
            parts = self._base_unique_id.split('_')
            host_name = parts[1] if len(parts) >= 2 else "Unknown Host"
            account_id_suffix = parts[2] if len(parts) >= 3 else "Unknown Account"
            configuration_url = f"https://{host_name}/" if host_name != "Unknown Host" else None
        except (IndexError, Exception):
            host_name = "Unknown Host"
            account_id_suffix = "Unknown Account"
            configuration_url = None

        return {
            "identifiers": {(DOMAIN, self._base_unique_id)},
            "name": f"{host_name} ({account_id_suffix})",
            "manufacturer": "gagata",
            "model": "Energy Monitor",
            "configuration_url": configuration_url,
        }


class SmartHubEnergyDemandSensor(CoordinatorEntity, SensorEntity):
    """Representation of the SmartHub Energy demand sensor."""

    def __init__(self, coordinator, base_unique_id: str):
        super().__init__(coordinator)
        self._base_unique_id = base_unique_id

    @property
    def name(self) -> str:
        return "SmartHub Energy Demand"

    @property
    def unique_id(self) -> str:
        return f"{self._base_unique_id}_energy_demand"

    @property
    def state(self) -> Optional[float]:
        if self.coordinator.data is not None:
            demand = self.coordinator.data.get("current_energy_demand")
            if demand is not None:
                return demand
        return None

    @property
    def available(self) -> bool:
        """Return True if demand data is available."""
        return (self.coordinator.data is not None and 
                self.coordinator.data.get("current_energy_demand") is not None)

    @property
    def unit_of_measurement(self) -> str:
        return "kW"

    @property
    def device_class(self) -> str:
        return "power"

    @property
    def state_class(self) -> str:
        return "measurement"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            "icon": "mdi:flash",
        }
        # Add peak demand information if available
        if self.coordinator.data:
            peak_demand = self.coordinator.data.get("peak_energy_demand")
            if peak_demand is not None:
                attrs["peak_demand"] = peak_demand
                attrs["peak_demand_unit"] = "kW"
        return attrs

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """Return information about the device."""
        if not self._base_unique_id:
            return None

        try:
            parts = self._base_unique_id.split('_')
            host_name = parts[1] if len(parts) >= 2 else "Unknown Host"
            account_id_suffix = parts[2] if len(parts) >= 3 else "Unknown Account"
            configuration_url = f"https://{host_name}/" if host_name != "Unknown Host" else None
        except (IndexError, Exception):
            host_name = "Unknown Host"
            account_id_suffix = "Unknown Account"
            configuration_url = None

        return {
            "identifiers": {(DOMAIN, self._base_unique_id)},
            "name": f"{host_name} ({account_id_suffix})",
            "manufacturer": "gagata",
            "model": "Energy Monitor",
            "configuration_url": configuration_url,
        }
