"""Sensor platform for repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RepelBridgeDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up repeller sensor platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create sensor entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.extend([
            RepelBridgeRuntimeSensor(coordinator, bus_id, config_entry.entry_id),
            RepelBridgeCartridgeLifeSensor(coordinator, bus_id, config_entry.entry_id),
            RepelBridgeRepellerCountSensor(coordinator, bus_id, config_entry.entry_id),
        ])
    
    # No system sensors - only bus-specific sensors
    
    async_add_entities(entities)


class RepelBridgeSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for repeller sensors."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.bus_id = bus_id
        self.entry_id = entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        entry_short = self.entry_id.split('-')[0]
        return {
            "identifiers": {(DOMAIN, f"{self.entry_id}_bus_{self.bus_id}")},
            "name": f"RepelBridge {entry_short} Bus {self.bus_id}",
            "manufacturer": "RepelBridge",
            "model": "Repeller Controller",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.bus_id in self.coordinator.data.get("buses", {})
        )


class RepelBridgeRuntimeSensor(RepelBridgeSensorBase):
    """Sensor for cartridge runtime hours."""

    def __init__(self, coordinator: RepelBridgeDataUpdateCoordinator, bus_id: int, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, bus_id, entry_id)
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_runtime_hours"
        entry_short = entry_id.split('-')[0]
        self._attr_name = f"RepelBridge {entry_short} Bus {bus_id} Runtime Hours"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        return cartridge_data.get("runtime_hours", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        return {
            "bus_id": self.bus_id,
            "active_seconds": cartridge_data.get("active_seconds", 0),
        }


class RepelBridgeCartridgeLifeSensor(RepelBridgeSensorBase):
    """Sensor for cartridge life percentage."""

    def __init__(self, coordinator: RepelBridgeDataUpdateCoordinator, bus_id: int, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, bus_id, entry_id)
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_cartridge_life"
        entry_short = entry_id.split('-')[0]
        self._attr_name = f"RepelBridge {entry_short} Bus {bus_id} Cartridge Life"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        return cartridge_data.get("percent_left", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        warn_at_data = self.coordinator.data["buses"][self.bus_id]["warn_at"]
        
        return {
            "bus_id": self.bus_id,
            "runtime_hours": cartridge_data.get("runtime_hours", 0),
            "warn_at_hours": warn_at_data.get("warn_at_hours", 0),
        }


class RepelBridgeRepellerCountSensor(RepelBridgeSensorBase):
    """Sensor for number of connected repellers."""

    def __init__(self, coordinator: RepelBridgeDataUpdateCoordinator, bus_id: int, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, bus_id, entry_id)
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_repeller_count"
        entry_short = entry_id.split('-')[0]
        self._attr_name = f"RepelBridge {entry_short} Bus {bus_id} Device Count"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.available:
            return None
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        return bus_data.get("repeller_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        return {
            "bus_id": self.bus_id,
            "bus_state": bus_data.get("state", "unknown"),
        }


