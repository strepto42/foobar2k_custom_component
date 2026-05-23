"""Foobar2k Media Player."""
import asyncio
import logging

from aiohttp import ClientConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN, TIMEOUT
from .foobar2k import Foobar2k

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["media_player"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Connect to Foobar2k Server"""
    conf = entry.data

    foobar2k_api = await api_init(hass, conf[CONF_HOST], conf.get(CONF_PORT) or DEFAULT_PORT)
    if not foobar2k_api:
        return False

    hass.data.setdefault(DOMAIN, {}).update({entry.entry_id: foobar2k_api})
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