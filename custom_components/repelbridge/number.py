"""Number platform for Liv Repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RepelBridgeDataUpdateCoordinator, RepelBridgeAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Liv Repeller number platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api: RepelBridgeAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    
    # Create number entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.extend([
            RepelBridgeAutoShutoffNumber(coordinator, api, bus_id, config_entry.entry_id),
            RepelBridgeCartridgeWarnAtNumber(coordinator, api, bus_id, config_entry.entry_id),
        ])
    
    async_add_entities(entities)


class RepelBridgeNumberBase(CoordinatorEntity, NumberEntity):
    """Base class for Liv Repeller number entities."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.api = api
        self.bus_id = bus_id
        self.entry_id = entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"bus_{self.bus_id}")},
            "name": f"Bus {self.bus_id}",
            "manufacturer": "Liv",
            "model": "RepelBridge Controller",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.bus_id in self.coordinator.data.get("buses", {})
        )


class RepelBridgeAutoShutoffNumber(RepelBridgeNumberBase):
    """Number entity for auto shutoff setting."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the auto shutoff number entity."""
        super().__init__(coordinator, api, bus_id, entry_id)
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_auto_shutoff"
        entry_short = entry_id.split('-')[0]
        self._attr_name = f"RepelBridge {entry_short} Bus {bus_id} Auto Shutoff"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 960  # 16 hours in minutes
        self._attr_native_step = 1  # 1 minute steps
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.available:
            return None
        
        auto_shutoff_data = self.coordinator.data["buses"][self.bus_id]["auto_shutoff"]
        return auto_shutoff_data.get("auto_shutoff_minutes", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the auto shutoff value."""
        await self.api.set_auto_shutoff(self.bus_id, int(value))
        
        # Request data update
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        return {
            "bus_id": self.bus_id,
            "description": "Automatic shutoff time in minutes (0 = disabled)",
            "max_hours": 16,
        }


class RepelBridgeCartridgeWarnAtNumber(RepelBridgeNumberBase):
    """Number entity for cartridge warning threshold."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the cartridge warning number entity."""
        super().__init__(coordinator, api, bus_id, entry_id)
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_cartridge_warn_at"
        entry_short = entry_id.split('-')[0]
        self._attr_name = f"RepelBridge {entry_short} Bus {bus_id} Cartridge Warning"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 1000  # 1000 hours max
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.available:
            return None
        
        warn_at_data = self.coordinator.data["buses"][self.bus_id]["warn_at"]
        return warn_at_data.get("warn_at_hours", 97)

    async def async_set_native_value(self, value: float) -> None:
        """Set the cartridge warning threshold."""
        await self.api.set_warn_at(self.bus_id, int(value))
        
        # Request data update
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        return {
            "bus_id": self.bus_id,
            "description": "Cartridge replacement warning threshold in hours",
            "current_runtime_hours": cartridge_data.get("runtime_hours", 0),
            "percent_left": cartridge_data.get("percent_left", 0),
        }