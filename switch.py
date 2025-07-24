"""Switch platform for Liv Repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up Liv Repeller switch platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api: RepelBridgeAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    
    # Create switch entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.append(RepelBridgePowerSwitch(coordinator, api, bus_id))
    
    async_add_entities(entities)


class RepelBridgePowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Liv Repeller power switch."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.api = api
        self.bus_id = bus_id
        self._attr_unique_id = f"repelbridge_bus_{bus_id}_power"
        self._attr_name = f"Liv Repeller Bus {bus_id} Power"

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
        """Return true if switch is on."""
        if not self.available:
            return False
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        return bus_data.get("powered", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.available:
            return {}
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        cartridge_data = self.coordinator.data["buses"][self.bus_id]["cartridge"]
        
        return {
            "bus_id": self.bus_id,
            "bus_state": bus_data.get("state", "unknown"),
            "repeller_count": bus_data.get("repeller_count", 0),
            "runtime_hours": cartridge_data.get("runtime_hours", 0),
            "cartridge_percent_left": cartridge_data.get("percent_left", 0),
            "brightness": bus_data.get("brightness", 0),
            "color": bus_data.get("color", {}),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.api.set_power(self.bus_id, True)
        
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.api.set_power(self.bus_id, False)
        
        # Request data update
        await self.coordinator.async_request_refresh()