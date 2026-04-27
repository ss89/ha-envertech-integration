"""Constants for the OpenEVT integration."""

from homeassistant.const import Platform

DOMAIN = "openevt"
PLATFORMS = [Platform.SENSOR]
DEFAULT_NAME = "OpenEVT"

# Polling interval in seconds
UPDATE_INTERVAL = 5

# Supervisor API — try all known slug variants
SUPERVISOR_ADDON_SLUGS = ["4318a8eb_openevt"]
SUPERVISOR_ADDON_PORT = 9090

# Device identifiers
GATEWAY_DEVICE_ID = "openevt-gateway"
GATEWAY_DEVICE_NAME = "OpenEVT"
GATEWAY_DEVICE_MODEL = "OpenEVT Gateway"


def get_gateway_device_name(inverter_ids: set[str] | None) -> str:
    """Return the gateway device name with inverter ID suffix."""
    if inverter_ids:
        ids = ", ".join(sorted(inverter_ids))
        return f"OpenEVT Gateway {ids}"
    return "OpenEVT Gateway"


# Inverter data keys
KEY_INVERTER_ID = "InverterId"
KEY_MODULE1 = "Module1"
KEY_MODULE2 = "Module2"

# Module field names
FIELD_MODULE_ID = "ModuleId"
FIELD_FIRMWARE_VERSION = "FirmwareVersion"
FIELD_INPUT_VOLTAGE_DC = "InputVoltageDC"
FIELD_OUTPUT_POWER_AC = "OutputPowerAC"
FIELD_TOTAL_ENERGY = "TotalEnergy"
FIELD_TEMPERATURE = "Temperature"
FIELD_OUTPUT_VOLTAGE_AC = "OutputVoltageAC"
FIELD_OUTPUT_FREQUENCY_AC = "OutputFrequencyAC"
