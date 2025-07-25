"""The RepelBridge integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    SERVICE_RESET_CARTRIDGE,
    ATTR_BUS_ID,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
]


class RepelBridgeAPI:
    """API client for RepelBridge device."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.host = host
        self.session = session
        self.base_url = f"http://{host}"

    async def get_system_status(self) -> dict:
        """Get system status."""
        url = f"{self.base_url}/api/system/status"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_bus_status(self, bus_id: int) -> dict:
        """Get bus status."""
        url = f"{self.base_url}/api/bus/{bus_id}/status"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_cartridge_status(self, bus_id: int) -> dict:
        """Get cartridge status."""
        url = f"{self.base_url}/api/bus/{bus_id}/cartridge"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def set_power(self, bus_id: int, state: bool) -> dict:
        """Set bus power state."""
        url = f"{self.base_url}/api/bus/{bus_id}/power"
        data = {"state": str(state).lower()}
        async with self.session.post(url, data=data) as response:
            response.raise_for_status()
            return await response.json()

    async def set_brightness(self, bus_id: int, brightness: int) -> dict:
        """Set bus brightness (0-254)."""
        url = f"{self.base_url}/api/bus/{bus_id}/brightness"
        data = {"value": brightness}
        async with self.session.post(url, data=data) as response:
            response.raise_for_status()
            return await response.json()

    async def set_color(self, bus_id: int, red: int, green: int, blue: int) -> dict:
        """Set bus RGB color (0-255 each)."""
        url = f"{self.base_url}/api/bus/{bus_id}/color"
        data = {"red": red, "green": green, "blue": blue}
        async with self.session.post(url, data=data) as response:
            response.raise_for_status()
            return await response.json()

    async def reset_cartridge(self, bus_id: int) -> dict:
        """Reset cartridge tracking."""
        url = f"{self.base_url}/api/bus/{bus_id}/cartridge/reset"
        async with self.session.post(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_auto_shutoff(self, bus_id: int) -> dict:
        """Get auto shutoff setting."""
        url = f"{self.base_url}/api/bus/{bus_id}/auto_shutoff"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def set_auto_shutoff(self, bus_id: int, minutes: int) -> dict:
        """Set auto shutoff setting."""
        url = f"{self.base_url}/api/bus/{bus_id}/auto_shutoff"
        json_data = {"minutes": minutes}
        headers = {"Content-Type": "application/json"}
        async with self.session.post(url, json=json_data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def get_warn_at(self, bus_id: int) -> dict:
        """Get cartridge warning threshold."""
        url = f"{self.base_url}/api/bus/{bus_id}/warn_at"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def set_warn_at(self, bus_id: int, hours: int) -> dict:
        """Set cartridge warning threshold."""
        url = f"{self.base_url}/api/bus/{bus_id}/warn_at"
        json_data = {"hours": hours}
        headers = {"Content-Type": "application/json"}
        async with self.session.post(url, json=json_data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()


class RepelBridgeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: RepelBridgeAPI,
    ) -> None:
        """Initialize."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get system status first
            system_data = await self.api.get_system_status()
            
            # Get data for both buses
            data = {"system": system_data, "buses": {}}
            
            for bus_id in [0, 1]:
                try:
                    bus_status = await self.api.get_bus_status(bus_id)
                    cartridge_status = await self.api.get_cartridge_status(bus_id)
                    auto_shutoff = await self.api.get_auto_shutoff(bus_id)
                    warn_at = await self.api.get_warn_at(bus_id)
                    
                    data["buses"][bus_id] = {
                        "status": bus_status,
                        "cartridge": cartridge_status,
                        "auto_shutoff": auto_shutoff,
                        "warn_at": warn_at,
                    }
                except aiohttp.ClientError as err:
                    _LOGGER.warning("Error fetching bus %d data: %s", bus_id, err)
                    # Continue with other buses if one fails
                    continue
            
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RepelBridge from a config entry."""
    host = entry.data[CONF_HOST]
    session = async_get_clientsession(hass)
    
    api = RepelBridgeAPI(host, session)
    
    # Test connection
    try:
        await api.get_system_status()
    except Exception as err:
        _LOGGER.error("Failed to connect to RepelBridge at %s: %s", host, err)
        raise ConfigEntryNotReady from err
    
    coordinator = RepelBridgeDataUpdateCoordinator(hass, api)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def reset_cartridge_service(call: ServiceCall) -> None:
        """Handle reset cartridge service."""
        bus_id = call.data[ATTR_BUS_ID]
        try:
            await api.reset_cartridge(bus_id)
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to reset cartridge for bus %d: %s", bus_id, err)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_CARTRIDGE,
        reset_cartridge_service,
        schema=vol.Schema({vol.Required(ATTR_BUS_ID): vol.In([0, 1])}),
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove services if this was the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_RESET_CARTRIDGE)
    
    return unload_ok