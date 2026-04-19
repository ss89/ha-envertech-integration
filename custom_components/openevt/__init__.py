"""The OpenEVT integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import OpenEVTCoordinator

# Import diagnostics platform to ensure it's available
from . import diagnostics  # noqa: F401

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[Any]
) -> bool:
    """Set up OpenEVT from a config entry."""
    urls: list[str] = entry.data["urls"]
    serial_numbers: list[str] = entry.data["serial_numbers"]

    coordinator = OpenEVTCoordinator(hass, urls, serial_numbers)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry[Any]
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
