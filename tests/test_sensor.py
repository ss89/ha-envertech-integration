"""Tests for the OpenEVT sensor entities."""

from homeassistant.components.sensor import SensorStateClass

from custom_components.openevt.const import (
    DOMAIN,
    GATEWAY_DEVICE_ID,
    KEY_MODULE1,
    KEY_MODULE2,
)
from custom_components.openevt.coordinator import OpenEVTCoordinator
from custom_components.openevt.sensor import (
    MODULE_SENSOR_DESCRIPTIONS,
    OpenEVTSensorEntity,
    OpenEVTStatusSensor,
)


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
            "sw_version": "1/0",
        }

    def test_name_has_module_prefix(self, mock_coordinator):
        """Test entity name is prefixed with ModuleId."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.name == "M001 Dc Voltage"

    def test_name_module2_prefix(self, mock_coordinator):
        """Test entity name uses Module2 ModuleId."""
        entity = OpenEVTSensorEntity(
            mock_coordinator,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE2,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.name == "M002 Dc Voltage"

    def test_name_no_module_id(self, hass):
        """Test entity name falls back to description when no ModuleId."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {
            "31583078": {
                "InverterId": "31583078",
                "Module1": {"InputVoltageDC": 23.0},
                "Module2": {},
            }
        }
        coord.last_update_success = True

        entity = OpenEVTSensorEntity(
            coord,
            MODULE_SENSOR_DESCRIPTIONS[0],
            "31583078",
            KEY_MODULE1,
            "openevt-31583078",
            "OpenEVT 31583078",
        )
        assert entity.name == "Dc Voltage"

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


class TestOpenEVTStatusSensor:
    """Tests for OpenEVTStatusSensor."""

    def test_connected_status(self, mock_coordinator):
        """Test connected status."""
        entity = OpenEVTStatusSensor(mock_coordinator)
        assert entity.native_value == "connected"
        assert entity.available is True

    def test_disconnected_status(self, hass):
        """Test disconnected status."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {}
        coord.last_update_success = False

        entity = OpenEVTStatusSensor(coord)
        assert entity.native_value == "disconnected"
        assert entity.available is True

    def test_device_info(self, mock_coordinator):
        """Test gateway device info."""
        entity = OpenEVTStatusSensor(mock_coordinator)
        assert entity.device_info["identifiers"] == {(DOMAIN, GATEWAY_DEVICE_ID)}
        assert "OpenEVT Gateway" in entity.device_info["name"]
        assert entity.device_info["manufacturer"] == "OpenEVT"
        assert entity.device_info["model"] == "OpenEVT Gateway"

    def test_unique_id(self, mock_coordinator):
        """Test status unique ID."""
        entity = OpenEVTStatusSensor(mock_coordinator)
        assert entity.unique_id == f"{GATEWAY_DEVICE_ID}-status"


class TestOpenEVTInverterTotalEnergySensor:
    """Tests for OpenEVTInverterTotalEnergySensor (inverter device)."""

    def test_total_energy_value(self, mock_coordinator):
        """Test total energy sums across both modules of an inverter."""
        from custom_components.openevt.sensor import OpenEVTInverterTotalEnergySensor

        entity = OpenEVTInverterTotalEnergySensor(mock_coordinator, "31583078", "openevt-31583078", "OpenEVT 31583078")
        # Module1: 26.31, Module2: 22.25 = 48.56
        assert entity.native_value == 48.56
        assert entity.available is True

    def test_total_energy_no_data(self, hass):
        """Test total energy returns None when no data."""
        from custom_components.openevt.sensor import OpenEVTInverterTotalEnergySensor

        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {}
        coord.last_update_success = False

        entity = OpenEVTInverterTotalEnergySensor(coord, "31583078", "openevt-31583078", "OpenEVT 31583078")
        assert entity.native_value is None
        assert entity.available is False

    def test_total_energy_unique_id(self, mock_coordinator):
        """Test total energy unique ID."""
        from custom_components.openevt.sensor import OpenEVTInverterTotalEnergySensor

        entity = OpenEVTInverterTotalEnergySensor(mock_coordinator, "31583078", "openevt-31583078", "OpenEVT 31583078")
        assert entity.unique_id == "openevt-31583078-total-energy"

    def test_device_info_is_inverter(self, mock_coordinator):
        """Test total energy belongs to inverter device, not gateway."""
        from custom_components.openevt.sensor import OpenEVTInverterTotalEnergySensor

        entity = OpenEVTInverterTotalEnergySensor(mock_coordinator, "31583078", "openevt-31583078", "OpenEVT 31583078")
        assert entity.device_info["identifiers"] == {(DOMAIN, "openevt-31583078")}
        assert entity.device_info["manufacturer"] == "Envertech"
        assert entity.device_info["model"] == "Microinverter"


class TestModuleSensorDescriptions:
    """Tests for sensor description definitions."""

    def test_all_sensors_have_required_fields(self):
        """Test all sensor descriptions have required fields."""
        for desc in MODULE_SENSOR_DESCRIPTIONS:
            assert desc.key
            assert desc.translation_key
            assert desc.device_class is not None

    def test_total_energy_has_total_state_class(self):
        """Test total energy sensor has TOTAL state class."""
        energy_desc = next(d for d in MODULE_SENSOR_DESCRIPTIONS if d.key == "total_energy")
        assert energy_desc.state_class == SensorStateClass.TOTAL
