"""Foobar2k Media Player."""
import asyncio
import logging
import aiohttp

from custom_components.foobar2k.foobar2k import Foobar2k
import voluptuous as vol
from aiohttp import ClientConnectionError, ServerDisconnectedError

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TIMEOUT
from .const import DEFAULT_PORT, DOMAIN, TIMEOUT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle

from . import config_flow  # noqa: F401

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["media_player"]

async def async_setup(hass, config):
    """Integration is UI-only — nothing to do here.

    Historically this function tried to launch a config-entry import flow
    from YAML, but the integration has no YAML schema and the launcher
    issued duplicate flow inits. Kept as a no-op so older configs don't
    blow up.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Connect to Foobar2k Server"""
    conf = entry.data

    foobar2k_api = await api_init(hass, conf[CONF_HOST], conf.get(CONF_PORT) or DEFAULT_PORT)
    if not foobar2k_api:
        return False

    hass.data.setdefault(DOMAIN, {}).update({entry.entry_id: foobar2k_api})
    # hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, PLATFORM))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    hass.data[DOMAIN].pop(config_entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True

async def api_init(hass, host, port, timeout = TIMEOUT):
    """Init the Foobar2k Server."""

    session = async_get_clientsession(hass)
    try:
        _LOGGER.debug(f"We have host {host} port {port}")
        device = Foobar2k(session, host, port, timeout)

        await device.async_update()
    except asyncio.TimeoutError:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady
    except ClientConnectionError:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        return None

    return device

async def update_listener(hass, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)