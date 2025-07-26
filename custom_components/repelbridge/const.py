"""Constants for the RepelBridge integration."""

DOMAIN = "repelbridge"

# Configuration
CONF_BUS_COUNT = "bus_count"

# Default values
DEFAULT_BUS_COUNT = 2
DEFAULT_SCAN_INTERVAL = 30

# Entity types
# ENTITY_TYPES = ["light", "sensor", "switch", "number"]
ENTITY_TYPES = ["light", "sensor", "number"]

# Service names
SERVICE_RESET_CARTRIDGE = "reset_cartridge"

# Attribute names
ATTR_BUS_ID = "bus_id"
ATTR_RUNTIME_HOURS = "runtime_hours"
ATTR_PERCENT_LEFT = "percent_left"
ATTR_AUTO_SHUTOFF = "auto_shutoff_seconds"
ATTR_WARN_AT_HOURS = "warn_at_hours"