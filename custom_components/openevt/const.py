"""Constants for the OpenEVT integration."""

from homeassistant.const import Platform

DOMAIN = "openevt"
PLATFORMS = [Platform.SENSOR]
DEFAULT_NAME = "OpenEVT"

# Polling interval in seconds
UPDATE_INTERVAL = 5

# Supervisor API
SUPERVISOR_ADDON_SLUG = "openevt"
SUPERVISOR_ADDON_PORT = 9090

# Device identifiers
GATEWAY_DEVICE_ID = "openevt-gateway"
GATEWAY_DEVICE_NAME = "OpenEVT"
GATEWAY_DEVICE_MODEL = "OpenEVT Gateway"

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
