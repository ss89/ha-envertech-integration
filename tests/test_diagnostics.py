"""Tests for the OpenEVT diagnostics module."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from custom_components.openevt.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
    _redact,
)
from custom_components.openevt.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


class TestRedact:
    """Tests for _redact function."""

    def test_redact_urls(self):
        """Test URLs are redacted."""
        data = {"urls": ["http://openevt:9090/inverter"], "other": "value"}
        result = _redact(data)
        assert result["urls"] == "REDACTED"
        assert result["other"] == "value"

    def test_redact_no_urls(self):
        """Test no URLs to redact."""
        data = {"other": "value"}
        result = _redact(data)
        assert result == data

    def test_redact_empty(self):
        """Test empty dict."""
        assert _redact({}) == {}


class TestConfigEntryDiagnostics:
    """Tests for async_get_config_entry_diagnostics."""

    @pytest.mark.asyncio
    async def test_diagnostics_success(self, hass: HomeAssistant):
        """Test diagnostics with successful update."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        from custom_components.openevt.coordinator import OpenEVTCoordinator

        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {"31583078": {"InverterId": "31583078"}}
        coord.last_update_success = True
        coord.last_update_exception = None
        entry.runtime_data = coord

        result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["entry_data"]["urls"] == "REDACTED"
        assert result["coordinator_data"]["31583078"]["InverterId"] == "31583078"
        assert result["last_update_success"] is True
        assert result["last_update_exception"] is None

    @pytest.mark.asyncio
    async def test_diagnostics_failure(self, hass: HomeAssistant):
        """Test diagnostics with failed update."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        from custom_components.openevt.coordinator import OpenEVTCoordinator

        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {}
        coord.last_update_success = False
        coord.last_update_exception = Exception("Connection failed")
        entry.runtime_data = coord

        result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["last_update_success"] is False
        assert "Connection failed" in result["last_update_exception"]

    @pytest.mark.asyncio
    async def test_diagnostics_no_coordinator(self, hass: HomeAssistant):
        """Test diagnostics when coordinator is None."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)
        entry.runtime_data = None

        result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["last_update_success"] is False
        assert result["last_update_exception"] is None


class TestDeviceDiagnostics:
    """Tests for async_get_device_diagnostics."""

    @pytest.mark.asyncio
    async def test_diagnostics_with_device(self, hass: HomeAssistant):
        """Test diagnostics for a specific device."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        from custom_components.openevt.coordinator import OpenEVTCoordinator

        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {
            "31583078": {
                "InverterId": "31583078",
                "Module1": {"InputVoltageDC": 23.64},
            }
        }
        coord.last_update_success = True
        entry.runtime_data = coord

        # Create a mock device entry
        device = MagicMock(spec=DeviceEntry)
        device.identifiers = {("openevt", "openevt-31583078")}

        result = await async_get_device_diagnostics(hass, entry, device)

        assert result["entry_data"]["urls"] == "REDACTED"
        assert result["device_inverter_id"] == "31583078"
        assert result["coordinator_data"]["InverterId"] == "31583078"
        assert result["coordinator_data"]["Module1"]["InputVoltageDC"] == 23.64

    @pytest.mark.asyncio
    async def test_diagnostics_unknown_device(self, hass: HomeAssistant):
        """Test diagnostics for unknown device."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        from custom_components.openevt.coordinator import OpenEVTCoordinator

        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        coord.data = {"31583078": {"InverterId": "31583078"}}
        entry.runtime_data = coord

        device = MagicMock(spec=DeviceEntry)
        device.identifiers = {("openevt", "openevt-999999")}

        result = await async_get_device_diagnostics(hass, entry, device)

        assert result["device_inverter_id"] == "999999"
        assert result["coordinator_data"] == {}
