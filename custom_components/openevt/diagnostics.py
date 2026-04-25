"""Diagnostics for the OpenEVT integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TO_REDACT = ["urls"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "entry_data": _redact(entry.data),
        "coordinator_data": coordinator.data if coordinator else {},
        "last_update_success": coordinator.last_update_success if coordinator else False,
        "last_update_exception": str(coordinator.last_update_exception)
        if coordinator and coordinator.last_update_exception
        else None,
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    coordinator = entry.runtime_data

    # Find the inverter ID for this device
    device_inverter_id = None
    for identifier in device.identifiers:
        if identifier[0] == DOMAIN and identifier[1].startswith("openevt-"):
            device_inverter_id = identifier[1].replace("openevt-", "")
            break

    return {
        "entry_data": _redact(entry.data),
        "device_inverter_id": device_inverter_id,
        "coordinator_data": coordinator.data.get(device_inverter_id, {})
        if coordinator
        else {},
    }


def _redact(data: Mapping[str, Any]) -> dict[str, Any]:
    """Redact sensitive data."""
    return {k: "REDACTED" if k in TO_REDACT else v for k, v in data.items()}
