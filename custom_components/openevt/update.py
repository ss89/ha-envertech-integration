"""Update entities for the OpenEVT integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.update import UpdateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    GATEWAY_DEVICE_ID,
    GATEWAY_DEVICE_MODEL,
    get_gateway_device_name,
)
from .coordinator import OpenEVTCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_gateway_device_info(coordinator: OpenEVTCoordinator) -> dict[str, Any]:
    """Return device info for the gateway device."""
    return {
        "identifiers": {(DOMAIN, GATEWAY_DEVICE_ID)},
        "name": get_gateway_device_name(coordinator.inverter_ids),
        "manufacturer": "OpenEVT",
        "model": GATEWAY_DEVICE_MODEL,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenEVT update entities from config entry."""
    coordinator: OpenEVTCoordinator = entry.runtime_data
    async_add_entities([OpenEVTFirmwareUpdateEntity(coordinator)])


class OpenEVTFirmwareUpdateEntity(CoordinatorEntity[OpenEVTCoordinator], UpdateEntity):
    """Firmware update entity for the gateway device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_supported_features = 0  # No install support yet

    def __init__(self, coordinator: OpenEVTCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{GATEWAY_DEVICE_ID}-firmware-update"
        self._attr_device_info = _get_gateway_device_info(coordinator)

    @property
    def name(self) -> str:
        """Return the entity name."""
        return "Firmware Update"

    @property
    def installed_version(self) -> str | None:
        """Return the currently installed firmware version."""
        for inverter_data in self.coordinator.data.values():
            for module_key in ("Module1", "Module2"):
                module_data = inverter_data.get(module_key, {})
                fw = module_data.get("FirmwareVersion")
                if fw:
                    return str(fw)
        return None

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version."""
        return None

    @property
    def in_progress(self) -> bool:
        """Return whether an update is in progress."""
        return False
