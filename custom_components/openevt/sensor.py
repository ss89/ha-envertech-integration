"""Sensor entities for the OpenEVT integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
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
    GATEWAY_DEVICE_MODEL,
    KEY_MODULE1,
    KEY_MODULE2,
    get_gateway_device_name,
)
from .coordinator import OpenEVTCoordinator

# Coordinator centralizes data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class OpenEVTSensorEntityDescription(SensorEntityDescription):
    """A class that describes sensor entities for Envertech inverters."""

    module: str = field(default="")
    value_fn: Callable[[dict[str, Any]], Any | None] = field(default=lambda data: data)


MODULE_SENSOR_DESCRIPTIONS: list[OpenEVTSensorEntityDescription] = [
    OpenEVTSensorEntityDescription(
        key="dc_voltage",
        translation_key="dc_voltage",
        module=FIELD_INPUT_VOLTAGE_DC,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement="V",
        value_fn=lambda d: d.get(FIELD_INPUT_VOLTAGE_DC),
    ),
    OpenEVTSensorEntityDescription(
        key="ac_voltage",
        translation_key="ac_voltage",
        module=FIELD_OUTPUT_VOLTAGE_AC,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement="V",
        value_fn=lambda d: d.get(FIELD_OUTPUT_VOLTAGE_AC),
    ),
    OpenEVTSensorEntityDescription(
        key="power",
        translation_key="power",
        module=FIELD_OUTPUT_POWER_AC,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement="W",
        value_fn=lambda d: d.get(FIELD_OUTPUT_POWER_AC),
    ),
    OpenEVTSensorEntityDescription(
        key="frequency",
        translation_key="frequency",
        module=FIELD_OUTPUT_FREQUENCY_AC,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement="Hz",
        value_fn=lambda d: d.get(FIELD_OUTPUT_FREQUENCY_AC),
    ),
    OpenEVTSensorEntityDescription(
        key="total_energy",
        translation_key="total_energy",
        module=FIELD_TOTAL_ENERGY,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement="kWh",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: d.get(FIELD_TOTAL_ENERGY),
    ),
    OpenEVTSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        module=FIELD_TEMPERATURE,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="\u00b0C",
        value_fn=lambda d: d.get(FIELD_TEMPERATURE),
    ),
]


def _get_gateway_device_info(coordinator: OpenEVTCoordinator) -> dict[str, Any]:
    """Return device info for the gateway device with dynamic name."""
    return {
        "identifiers": {(DOMAIN, GATEWAY_DEVICE_ID)},
        "name": get_gateway_device_name(coordinator.inverter_ids),
        "manufacturer": "OpenEVT",
        "model": GATEWAY_DEVICE_MODEL,
    }


def _create_inverter_entities(
    coordinator: OpenEVTCoordinator,
    inverter_id: str,
    async_add_entities: AddEntitiesCallback,
    entity_list: list[OpenEVTSensorEntity] | None = None,
) -> None:
    """Create sensor entities for a single inverter."""
    device_id = f"openevt-{inverter_id}"
    device_name = f"OpenEVT {inverter_id}"

    created: list[OpenEVTSensorEntity] = []
    for module_key in (KEY_MODULE1, KEY_MODULE2):
        for desc in MODULE_SENSOR_DESCRIPTIONS:
            entity = OpenEVTSensorEntity(
                coordinator,
                desc,
                inverter_id,
                module_key,
                device_id,
                device_name,
            )
            created.append(entity)

    # Add total energy sensor for the inverter
    total_energy_entity = OpenEVTInverterTotalEnergySensor(coordinator, inverter_id, device_id, device_name)
    created.append(total_energy_entity)

    async_add_entities(created)
    if entity_list is not None:
        entity_list.extend(created)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenEVT sensors from config entry."""
    coordinator: OpenEVTCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    known_inverter_ids: set[str] = set()
    inverter_entities: dict[str, list[OpenEVTSensorEntity]] = {}

    # Gateway entities
    entities.append(OpenEVTStatusSensor(coordinator))
    entities.append(OpenEVTLastUpdateSensor(coordinator))
    entities.append(OpenEVTResponseTimeSensor(coordinator))
    entities.append(OpenEVTConsecutiveFailuresSensor(coordinator))

    # Per-inverter devices (keys are InverterId from coordinator.data)
    for inverter_id in coordinator.data:
        inverter_entities[inverter_id] = []
        _create_inverter_entities(coordinator, inverter_id, async_add_entities, inverter_entities[inverter_id])

    async_add_entities(entities)

    def _on_coordinator_update() -> None:
        nonlocal known_inverter_ids
        """Handle coordinator data updates — add/remove inverter entities."""
        current_ids = set(coordinator.data.keys())
        new_ids = current_ids - known_inverter_ids
        stale_ids = known_inverter_ids - current_ids

        if not new_ids and not stale_ids:
            return

        _LOGGER.info(
            "Inverter list changed: +%s, -%s (current: %s)",
            new_ids,
            stale_ids,
            current_ids,
        )

        for inverter_id in new_ids:
            inverter_entities[inverter_id] = []
            _create_inverter_entities(coordinator, inverter_id, async_add_entities, inverter_entities[inverter_id])

        for inverter_id in stale_ids:
            for entity in inverter_entities.pop(inverter_id, []):
                hass.add_job(entity.async_remove())

        known_inverter_ids.update(new_ids)
        known_inverter_ids -= stale_ids

    coordinator.async_add_listener(_on_coordinator_update)


class OpenEVTSensorEntity(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Base entity for OpenEVT sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenEVTCoordinator,
        description: OpenEVTSensorEntityDescription,
        inverter_id: str,
        module: str,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._inverter_id = inverter_id
        self._module = module
        self._attr_unique_id = f"{inverter_id}-{module}-{description.key}"
        firmware_version = self._get_first_module_firmware()
        device_info: dict[str, Any] = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Envertech",
            "model": "Microinverter",
        }
        if firmware_version:
            device_info["sw_version"] = firmware_version
        self._attr_device_info = device_info

    def _get_first_module_firmware(self) -> str | None:
        """Return the firmware version from the first available module."""
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        for module_key in (KEY_MODULE1, KEY_MODULE2):
            module_data = inverter_data.get(module_key, {})
            fw = module_data.get(FIELD_FIRMWARE_VERSION)
            if fw:
                return str(fw)
        return None

    @property
    def name(self) -> str | None:
        """Return entity name prefixed with ModuleId."""
        module_id = self._get_module_id()
        desc_name = self.entity_description.name
        if desc_name is None or not isinstance(desc_name, str):
            desc_name = self.entity_description.key.replace("_", " ").title()
        if module_id:
            return f"{module_id} {desc_name}"
        return desc_name

    def _get_module_id(self) -> str | None:
        """Return the ModuleId value from module data."""
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        module_data = inverter_data.get(self._module, {})
        return module_data.get(FIELD_MODULE_ID)

    @property
    def native_value(self):
        """Return the native value."""
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        module_data = inverter_data.get(self._module, {})
        return getattr(self.entity_description, "value_fn", lambda d: d)(module_data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        module_data = inverter_data.get(self._module, {})
        value = getattr(self.entity_description, "value_fn", lambda d: d)(module_data)
        return value is not None


class OpenEVTStatusSensor(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Connection status sensor for the gateway device."""

    _attr_has_entity_name = True
    _attr_translation_key = "connection_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options: ClassVar[list[str]] = ["connected", "disconnected"]  # type: ignore[misc]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OpenEVTCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{GATEWAY_DEVICE_ID}-status"
        self._attr_device_info = _get_gateway_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        """Return connection status."""
        if self.coordinator.last_update_success and self.coordinator.data:
            return "connected"
        return "disconnected"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


class OpenEVTLastUpdateSensor(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Last successful update timestamp sensor for the gateway device."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OpenEVTCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{GATEWAY_DEVICE_ID}-last-update"
        self._attr_device_info = _get_gateway_device_info(coordinator)

    @property
    def native_value(self) -> datetime | None:
        """Return last update time."""
        return self.coordinator.last_contact

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


class OpenEVTResponseTimeSensor(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Response time sensor for the gateway device."""

    _attr_has_entity_name = True
    _attr_translation_key = "response_time"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "ms"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OpenEVTCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{GATEWAY_DEVICE_ID}-response-time"
        self._attr_device_info = _get_gateway_device_info(coordinator)

    @property
    def native_value(self) -> float | None:
        """Return response time in milliseconds."""
        return self.coordinator.response_time_ms if self.coordinator.last_update_success else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


class OpenEVTConsecutiveFailuresSensor(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Consecutive failed request count sensor for the gateway device."""

    _attr_has_entity_name = True
    _attr_translation_key = "retries"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options: ClassVar[list[str]] = ["0", "1", "2", "3", "4+"]  # type: ignore[misc]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OpenEVTCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{GATEWAY_DEVICE_ID}-consecutive-failures"
        self._attr_device_info = _get_gateway_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        """Return consecutive failure count as string option."""
        retries = self.coordinator.request_retries if self.coordinator.last_update_success else 0
        return str(min(retries, 4))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True


class OpenEVTInverterTotalEnergySensor(CoordinatorEntity[OpenEVTCoordinator], SensorEntity):
    """Total energy sensor for an inverter, summing both modules."""

    _attr_has_entity_name = True
    _attr_translation_key = "total_energy_combined"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: OpenEVTCoordinator,
        inverter_id: str,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._inverter_id = inverter_id
        self._attr_unique_id = f"{device_id}-total-energy"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Envertech",
            "model": "Microinverter",
        }
        firmware_version = self._get_first_module_firmware()
        if firmware_version:
            self._attr_device_info["sw_version"] = firmware_version

    def _get_first_module_firmware(self) -> str | None:
        """Return the firmware version from the first available module."""
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        for module_key in (KEY_MODULE1, KEY_MODULE2):
            module_data = inverter_data.get(module_key, {})
            fw = module_data.get(FIELD_FIRMWARE_VERSION)
            if fw:
                return str(fw)
        return None

    @property
    def native_value(self) -> float | None:
        """Return total energy summed across both modules of this inverter."""
        inverter_data = self.coordinator.data.get(self._inverter_id, {})
        total = 0.0
        has_data = False
        for module_key in (KEY_MODULE1, KEY_MODULE2):
            module_data = inverter_data.get(module_key, {})
            energy = module_data.get(FIELD_TOTAL_ENERGY)
            if energy is not None:
                total += energy
                has_data = True
        if has_data:
            return round(total, 2)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and bool(self.coordinator.data.get(self._inverter_id))
