"""Button platform for repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up repeller button platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api: RepelBridgeAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    
    # Create button entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.append(RepelBridgeResetCartridgeButton(coordinator, api, bus_id, config_entry.entry_id))
    
    async_add_entities(entities)


class RepelBridgeResetCartridgeButton(CoordinatorEntity, ButtonEntity):
    """Representation of a cartridge reset button."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.api = api
        self.bus_id = bus_id
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_reset_cartridge"
        entry_short = entry_id.split('-')[0]
        self.entity_id = f"{entry_short}_bus_{bus_id}_reset_cartridge"
        self._attr_name = f"Bus {bus_id} Reset Cartridge"
        self._attr_icon = "mdi:restore"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        entry_short = self.coordinator.config_entry.entry_id.split('-')[0]
        return {
            "identifiers": {(DOMAIN, f"{self.coordinator.config_entry.entry_id}_bus_{self.bus_id}")},
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

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.api.reset_cartridge(self.bus_id)
            _LOGGER.info("Successfully reset cartridge for bus %d", self.bus_id)
            
            # Request data update to reflect the reset
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to reset cartridge for bus %d: %s", self.bus_id, err)
            raise