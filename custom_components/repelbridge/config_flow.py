"""Config flow for RepelBridge integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default="RepelBridge"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    host = data[CONF_HOST]
    
    # Test connection by fetching system status
    try:
        url = f"http://{host}/api/system/status"
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                raise CannotConnect
            
            system_data = await response.json()
            if "device_name" not in system_data:
                raise InvalidHost
                
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to RepelBridge at %s: %s", host, err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error connecting to RepelBridge at %s: %s", host, err)
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_NAME], "host": host}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RepelBridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(self, discovery_info) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        name = discovery_info.name.replace("._repelbridge._tcp.local.", "")
        
        # Check if already configured
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()
        
        # Try to validate the discovered device
        try:
            await validate_input(self.hass, {CONF_HOST: host, CONF_NAME: name})
        except (CannotConnect, InvalidHost):
            return self.async_abort(reason="cannot_connect")
        
        # Store the host and name for the confirmation step
        self.context.update({
            "title_placeholders": {"name": name},
            "discovered_host": host,
            "discovered_name": name
        })
        
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a confirmation flow initiated by zeroconf."""
        if user_input is not None:
            host = self.context.get("discovered_host") or self.context["unique_id"]
            name = self.context.get("discovered_name") or self.context["title_placeholders"]["name"]
            
            return self.async_create_entry(
                title=name,
                data={CONF_HOST: host, CONF_NAME: name},
            )

        # Direct confirmation without relying on strings.json
        name = self.context.get("discovered_name", "RepelBridge")
        
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({}),
            description=f"Do you want to add the RepelBridge device '{name}' to Home Assistant? This will allow you to control Liv Repeller devices and monitor cartridge life.",
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate there is invalid host."""