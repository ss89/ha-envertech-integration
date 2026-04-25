"""Tests for the OpenEVT integration __init__ module."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.openevt import async_setup_entry, async_unload_entry
from custom_components.openevt.coordinator import OpenEVTCoordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_setup_entry_success(self, hass: HomeAssistant):
        """Test successful setup."""
        entry = MockConfigEntry(
            domain="openevt",
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.openevt.coordinator.OpenEVTCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ):
            result = await async_setup_entry(hass, entry)

        assert result is True
        assert entry.runtime_data is not None
        assert isinstance(entry.runtime_data, OpenEVTCoordinator)

    @pytest.mark.asyncio
    async def test_setup_entry_stores_coordinator(self, hass: HomeAssistant):
        """Test coordinator is stored in runtime_data."""
        entry = MockConfigEntry(
            domain="openevt",
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.openevt.coordinator.OpenEVTCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ):
            await async_setup_entry(hass, entry)

        assert hasattr(entry, "runtime_data")
        assert isinstance(entry.runtime_data, OpenEVTCoordinator)


class TestAsyncUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.mark.asyncio
    async def test_unload_entry_success(self, hass: HomeAssistant):
        """Test successful unload."""
        entry = MockConfigEntry(
            domain="openevt",
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.openevt.coordinator.OpenEVTCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ):
            await async_setup_entry(hass, entry)

        with patch.object(
            hass.config_entries, "async_unload_platforms", return_value=True
        ):
            result = await async_unload_entry(hass, entry)

        assert result is True

    @pytest.mark.asyncio
    async def test_unload_entry_failure(self, hass: HomeAssistant):
        """Test unload failure."""
        entry = MockConfigEntry(
            domain="openevt",
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.openevt.coordinator.OpenEVTCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ):
            await async_setup_entry(hass, entry)

        with patch.object(
            hass.config_entries, "async_unload_platforms", return_value=False
        ):
            result = await async_unload_entry(hass, entry)

        assert result is False
