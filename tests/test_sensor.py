"""Tests for the OpenEVT sensor entities."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.openevt.const import (
    DOMAIN,
    FIELD_FIRMWARE_VERSION,
    FIELD_INPUT_VOLTAGE_DC,
    FIELD_MODULE_ID,
    FIELD_OUTPUT_FREQUENCY_AC,
    FIELD_OUTPUT_POWER_AC,
    FIELD_OUTPUT_VOLTAGE_AC,
    FIELD_TEMPERATURE,
    FIELD_TOTAL_ENERGY,
    GATEWAY_DEVICE_ID,
    KEY_MODULE1,
    KEY_MODULE2,
)
from custom_components.openevt.sensor import (
    MODULE_INFO_DESCRIPTIONS,
    MODULE_SENSOR_DESCRIPTIONS,
    OpenEVTConnectionStatusSensor,
    OpenEVTInverterIDSensor,
    OpenEVTSensorEntity,
)
from custom_components.openevt.coordinator import OpenEVTCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry



class TestOpenEVTSensorEntity:
    """Tests for OpenEVTSensorEntity."""

    def test_dc_voltage_value(self, mock_coordinator):
        """Test DC voltage sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 23.64

    def test_ac_voltage_value(self, mock_coordinator):
        """Test AC voltage sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[1],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 233.97

    def test_power_value(self, mock_coordinator):
        """Test power sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[2],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 3.59

    def test_frequency_value(self, mock_coordinator):
        """Test frequency sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[3],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 49.97

    def test_total_energy_value(self, mock_coordinator):
        """Test total energy sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[4],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 26.31

    def test_temperature_value(self, mock_coordinator):
        """Test temperature sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[5],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == 29.40

    def test_module_id_value(self, mock_coordinator):
        """Test module ID sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_INFO_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == "M001"

    def test_firmware_version_value(self, mock_coordinator):
        """Test firmware version sensor value."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_INFO_DESCRIPTIONS[1],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.native_value == "1/0"

    def test_module2_values(self, mock_coordinator):
        """Test Module2 sensor values."""
        for desc in MODULE_SENSOR_DESCRIPTIONS:
            entity = OpenEVTSensorEntity(
                mock_coordinator,
                desc,
                "31583078",
                KEY_MODULE2,
                "openevt-31583078",
                "OpenEVT 31583078",
            )
            assert entity.native_value is not None

    def test_entity_unique_id(self, mock_coordinator):
        """Test unique ID format."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.unique_id == "31583078-Module1-dc_voltage"

    def test_device_info(self, mock_coordinator):
        """Test device info."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.device_info == {
            "identifiers": {(DOMAIN, "openevt-31583078")},
            "name": "OpenEVT 31583078",
            "manufacturer": "Envertech",
            "model": "Microinverter",
        }

    def test_available_when_connected(self, mock_coordinator):
        """Test entity is available when connected."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.available is True

    def test_available_when_no_data(self, mock_coordinator):
        """Test entity unavailable when module data missing."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            "NonExistentModule",
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.available is False

    def test_available_when_update_failed(self, hass):
        """Test entity unavailable when last update failed."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {}
        coord.last_update_success = False

        entity = OpenEVTSensorEntity(
            coord,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.available is False


class TestOpenEVTConnectionStatusSensor:
    """Tests for OpenEVTConnectionStatusSensor."""

    def test_connected_status(self, mock_coordinator):
        """Test connected status."""
        entity = OpenEVTConnectionStatusSensor(mock_coordinator)
        assert entity.native_value == "connected"
        assert entity.available is True

    def test_disconnected_status(self, hass):
        """Test disconnected status."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {}
        coord.last_update_success = False

        entity = OpenEVTConnectionStatusSensor(coord)
        assert entity.native_value == "disconnected"
        assert entity.available is True

    def test_device_info(self, mock_coordinator):
        """Test gateway device info."""
        entity = OpenEVTConnectionStatusSensor(mock_coordinator)
        assert entity.device_info == {
            "identifiers": {(DOMAIN, GATEWAY_DEVICE_ID)},
            "name": "OpenEVT",
            "manufacturer": "OpenEVT",
            "model": "OpenEVT Gateway",
        }

    def test_unique_id(self, mock_coordinator):
        """Test connection status unique ID."""
        entity = OpenEVTConnectionStatusSensor(mock_coordinator)
        assert entity.unique_id == f"{GATEWAY_DEVICE_ID}-connection-status"


class TestOpenEVTInverterIDSensor:
    """Tests for OpenEVTInverterIDSensor."""

    def test_inverter_id_value(self, mock_coordinator):
        """Test inverter ID sensor value."""
        entity = OpenEVTInverterIDSensor(mock_coordinator)
        assert entity.native_value == "31583078"

    def test_inverter_id_device_info(self, mock_coordinator):
        """Test inverter ID gateway device info."""
        entity = OpenEVTInverterIDSensor(mock_coordinator)
        assert entity.device_info == {
            "identifiers": {(DOMAIN, GATEWAY_DEVICE_ID)},
            "name": "OpenEVT",
            "manufacturer": "OpenEVT",
            "model": "OpenEVT Gateway",
        }


class TestModuleSensorDescriptions:
    """Tests for sensor description definitions."""

    def test_all_sensors_have_required_fields(self):
        """Test all sensor descriptions have required fields."""
        for desc in MODULE_SENSOR_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.device_class is not None

    def test_info_sensors_have_diagnostics_category(self):
        """Test info sensors have DIAGNOSTIC category."""
        for desc in MODULE_INFO_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.entity_category is not None

    def test_total_energy_has_total_state_class(self):
        """Test total energy sensor has TOTAL state class."""
        energy_desc = next(
            d for d in MODULE_SENSOR_DESCRIPTIONS if d.key == "total_energy"
        )
        assert energy_desc.state_class == SensorStateClass.TOTAL
