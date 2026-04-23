"""Fixtures for OpenEVT integration tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.openevt.const import DOMAIN
from custom_components.openevt.coordinator import OpenEVTCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_supervisor_response():
    """Return a mock Supervisor addon response."""
    return {
        "data": {
            "slug": "openevt",
            "state": "started",
            "hostname": "openevt",
            "options": {},
        }
    }


@pytest.fixture
def mock_inverter_data():
    """Return sample inverter JSON data (raw API format)."""
    return {
        "InverterId": "31583078",
        "Module1": {
            "ModuleId": "M001",
            "FirmwareVersion": "1/0",
            "InputVoltageDC": 23.64,
            "OutputPowerAC": 3.59,
            "TotalEnergy": 26.31,
            "Temperature": 29.40,
            "OutputVoltageAC": 233.97,
            "OutputFrequencyAC": 49.97,
        },
        "Module2": {
            "ModuleId": "M002",
            "FirmwareVersion": "1/0",
            "InputVoltageDC": 24.08,
            "OutputPowerAC": 3.56,
            "TotalEnergy": 22.25,
            "Temperature": 30.20,
            "OutputVoltageAC": 233.97,
            "OutputFrequencyAC": 49.97,
        },
    }


@pytest.fixture
def mock_parsed_coordinator_data():
    """Return parsed inverter data in coordinator format (InverterId as key)."""
    return {
        "31583078": {
            "InverterId": "31583078",
            "Module1": {
                "ModuleId": "M001",
                "FirmwareVersion": "1/0",
                "InputVoltageDC": 23.64,
                "OutputPowerAC": 3.59,
                "TotalEnergy": 26.31,
                "Temperature": 29.40,
                "OutputVoltageAC": 233.97,
                "OutputFrequencyAC": 49.97,
            },
            "Module2": {
                "ModuleId": "M002",
                "FirmwareVersion": "1/0",
                "InputVoltageDC": 24.08,
                "OutputPowerAC": 3.56,
                "TotalEnergy": 22.25,
                "Temperature": 30.20,
                "OutputVoltageAC": 233.97,
                "OutputFrequencyAC": 49.97,
            },
        }
    }


@pytest.fixture
def mock_parsed_coordinator_data_single():
    """Return parsed inverter data with single inverter."""
    return {
        "111111": {
            "InverterId": "111111",
            "Module1": {"ModuleId": "M001", "InputVoltageDC": 23.0},
            "Module2": {"ModuleId": "M002", "InputVoltageDC": 24.0},
        }
    }


@pytest.fixture
def mock_parsed_coordinator_data_multi():
    """Return parsed inverter data with multiple inverters."""
    return {
        "111111": {
            "InverterId": "111111",
            "Module1": {"InputVoltageDC": 23.0},
            "Module2": {"InputVoltageDC": 24.0},
        },
        "222222": {
            "InverterId": "222222",
            "Module1": {"InputVoltageDC": 25.0},
            "Module2": {"InputVoltageDC": 26.0},
        },
    }


@pytest.fixture
def mock_inverter_data_no_id():
    """Return invalid inverter data missing InverterId."""
    return {
        "Module1": {
            "ModuleId": "M001",
        },
    }


@pytest.fixture
def mock_supervisor_not_started():
    """Return a mock Supervisor addon response with addon stopped."""
    return {
        "data": {
            "slug": "openevt",
            "state": "stopped",
            "hostname": "openevt",
            "options": {},
        }
    }


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"urls": ["http://openevt:9090/inverter"]},
        version=1,
    )
    return entry


@pytest.fixture
def mock_coordinator(hass, mock_parsed_coordinator_data):
    """Create a mock coordinator with parsed data."""
    coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
    coord.data = mock_parsed_coordinator_data
    coord.last_update_success = True
    return coord
