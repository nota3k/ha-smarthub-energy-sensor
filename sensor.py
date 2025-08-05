"""SmartHub Energy Sensor platform for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    COST_SENSOR_SUFFIX,
    DOMAIN,
    ENERGY_SENSOR_SUFFIX,
    MANUFACTURER,
    MODEL,
    POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmartHubSensorEntityDescription(SensorEntityDescription):
    """Describes SmartHub sensor entity."""

    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[SmartHubSensorEntityDescription, ...] = (
    SmartHubSensorEntityDescription(
        key=ENERGY_SENSOR_SUFFIX,
        name="Energy Usage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="kWh",
        icon="mdi:power-plug",
        data_key="current_energy_usage",
    ),
    SmartHubSensorEntityDescription(
        key=COST_SENSOR_SUFFIX,
        name="Energy Cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="USD",
        icon="mdi:currency-usd",
        data_key="current_energy_cost",
    ),
)


def _parse_unique_id_components(unique_id: str) -> tuple[str, str, str | None]:
    """Parse unique_id components for device info."""
    try:
        parts = unique_id.split("_")
        host_name = parts[1] if len(parts) >= 2 else "Unknown Host"
        account_id_suffix = parts[2] if len(parts) >= 3 else "Unknown Account"
        configuration_url = (
            f"https://{host_name}/" if host_name != "Unknown Host" else None
        )
    except (IndexError, ValueError) as err:
        _LOGGER.warning("Error parsing unique_id '%s': %s", unique_id, err)
        host_name, account_id_suffix, configuration_url = (
            "Parsing Error",
            "Parsing Error",
            None,
        )
    else:
        return host_name, account_id_suffix, configuration_url

    return host_name, account_id_suffix, configuration_url


def _create_device_info(base_unique_id: str) -> DeviceInfo:
    """Create device info for SmartHub sensors."""
    host_name, account_id_suffix, configuration_url = _parse_unique_id_components(
        base_unique_id
    )

    device_info = DeviceInfo(
        identifiers={(DOMAIN, base_unique_id)},
        name=f"{host_name} ({account_id_suffix})",
        manufacturer=MANUFACTURER,
        model=MODEL,
    )

    if configuration_url:
        device_info["configuration_url"] = configuration_url

    return device_info


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]

    # Get base unique ID with fallback
    base_unique_id = config_entry.unique_id or config_entry.entry_id
    if not config_entry.unique_id:
        _LOGGER.warning(
            "Config entry unique_id is None for %s, falling back to entry_id",
            config_entry.entry_id,
        )

    # Create coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SmartHub Energy",
        update_method=api.get_energy_data,
        update_interval=POLL_INTERVAL,
        config_entry=config_entry,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create sensors from descriptions
    entities = [
        SmartHubSensor(coordinator, base_unique_id, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class SmartHubSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartHub sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        base_unique_id: str,
        description: SmartHubSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._description = description
        self._base_unique_id = base_unique_id
        self._attr_unique_id = f"{base_unique_id}_{description.key}"
        self._attr_device_info = _create_device_info(base_unique_id)

        # Set entity attributes based on sensor type
        if description.key == ENERGY_SENSOR_SUFFIX:
            self._attr_name = "Energy Usage"
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_native_unit_of_measurement = "kWh"
            self._attr_icon = "mdi:power-plug"
        elif description.key == COST_SENSOR_SUFFIX:
            self._attr_name = "Energy Cost"
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_state_class = SensorStateClass.TOTAL
            self._attr_native_unit_of_measurement = "USD"
            self._attr_icon = "mdi:currency-usd"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and self._description.data_key:
            return self.coordinator.data.get(self._description.data_key)
        return None

    @property
    def available(self) -> bool:
        """Return True if sensor data is available."""
        if not super().available or not self.coordinator.data:
            return False

        # For cost sensor, check if cost data is specifically available
        if self._description.key == COST_SENSOR_SUFFIX:
            return self.coordinator.data.get("current_energy_cost") is not None

        return True
