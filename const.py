"""Constants for the SmartHub integration."""

from datetime import timedelta

DOMAIN = "smarthub"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ACCOUNT_ID = "account_id"
CONF_LOCATION_ID = "location_id"
CONF_HOST = "host"

# Polling interval - 12 hours (not user-configurable per HA guidelines)
POLL_INTERVAL = timedelta(minutes=60)

# Device info constants
MANUFACTURER = "gagata"
MODEL = "Energy Monitor"

# Sensor suffixes for unique IDs
ENERGY_SENSOR_SUFFIX = "energy_usage"
COST_SENSOR_SUFFIX = "energy_cost"
