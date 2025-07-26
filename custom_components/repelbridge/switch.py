# """Switch platform for repeller integration."""
# from __future__ import annotations
#
# import logging
#
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
#
# _LOGGER = logging.getLogger(__name__)
#
#
# async def async_setup_entry(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     async_add_entities: AddEntitiesCallback,
# ) -> None:
#     """Set up repeller switch platform."""
#     # No switch entities - power control is handled by light entities only
#     async_add_entities([])