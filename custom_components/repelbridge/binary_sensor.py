"""Binary sensor platform for Liv Repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RepelBridgeDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default cartridge low threshold percentage
DEFAULT_CARTRIDGE_LOW_THRESHOLD = 5


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liv Repeller binary sensor platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create binary sensor entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.append(RepelBridgeCartridgeLowSensor(coordinator, bus_id))
    
    async_add_entities(entities)


class RepelBridgeCartridgeLowSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for cartridge low warning."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        bus_id: int,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.bus_id = bus_id
        self._attr_unique_id = f"repelbridge_bus_{bus_id}_cartridge_low"
        self._attr_name = f"Liv Repeller Bus {bus_id} Cartridge Low"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"bus_{self.bus_id}")},
            "name": f"Liv Repeller Bus {self.bus_id}",
            "manufacturer": "Liv",
            "model": "Repeller Device",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.bus_id in self.coordinator.data.get("buses", {})
        )

    @property
    def is_on(self) -> bool:
        """Return true if cartridge is low."""
        if not self.available:
            return False
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        percent_left = cartridge_data.get("percent_left", 100)
        
        # Use configurable threshold if available, otherwise use default
        threshold = self._get_threshold()
        
        return percent_left <= threshold

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.is_on:
            return "mdi:battery-alert"
        return "mdi:battery"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        
        return {
            "bus_id": self.bus_id,
            "percent_left": cartridge_data.get("percent_left", 100),
            "runtime_hours": cartridge_data.get("runtime_hours", 0),
            "threshold": self._get_threshold(),
        }

    def _get_threshold(self) -> int:
        """Get the cartridge low threshold percentage."""
        # For now, use the default threshold
        # TODO: This could be made configurable via a number entity
        return DEFAULT_CARTRIDGE_LOW_THRESHOLD