"""Light platform for repeller integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
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
    """Set up repeller light platform."""
    coordinator: RepelBridgeDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api: RepelBridgeAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    
    # Create light entities for both buses
    entities = []
    for bus_id in [0, 1]:
        entities.append(RepelBridgeLight(coordinator, api, bus_id, config_entry.entry_id))
    
    async_add_entities(entities)


class RepelBridgeLight(CoordinatorEntity, LightEntity):
    """Representation of a repeller light."""

    def __init__(
        self,
        coordinator: RepelBridgeDataUpdateCoordinator,
        api: RepelBridgeAPI,
        bus_id: int,
        entry_id: str,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self.api = api
        self.bus_id = bus_id
        self._attr_unique_id = f"{entry_id}_bus_{bus_id}_light"
        self._attr_has_entity_name = True
        self._attr_name = None  # None as this is the default entity for a RepelBridge Bus
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}

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

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if not self.available:
            return False
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        return bus_data.get("powered", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if not self.available:
            return None
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        # Device reports brightness in 0-254 range, HA expects 0-255
        repeller_brightness = bus_data.get("brightness", 0)
        # Scale from 0-254 to 0-255 (essentially just clamp to 255 max)
        return min(repeller_brightness, 255)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        if not self.available:
            return None
        
        bus_data = self.coordinator.data["buses"][self.bus_id]["status"]
        color = bus_data.get("color", {})
        
        return (
            color.get("red", 0),
            color.get("green", 0),
            color.get("blue", 0),
        )

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
            "auto_shutoff_seconds": cartridge_data.get("auto_shutoff_seconds", 0),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        # Handle brightness
        if ATTR_BRIGHTNESS in kwargs:
            # Convert from HA scale (0-255) to device scale (0-254)
            ha_brightness = kwargs[ATTR_BRIGHTNESS]
            repeller_brightness = min(ha_brightness, 254)
            await self.api.set_brightness(self.bus_id, repeller_brightness)
        
        # Handle RGB color
        if ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            await self.api.set_color(self.bus_id, red, green, blue)
        
        # Turn on the bus
        await self.api.set_power(self.bus_id, True)
        
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self.api.set_power(self.bus_id, False)
        
        # Request data update
        await self.coordinator.async_request_refresh()