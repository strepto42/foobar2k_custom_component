"""Fix #6: api_init and async_step_user must use HA's shared aiohttp
session, not a fresh one (which leaks)."""
from __future__ import annotations

import aiohttp
import pytest

import custom_components.foobar2k as init_module
from custom_components.foobar2k import config_flow as cf_module
from homeassistant.core import HomeAssistant


class _RecordingFoobar2k:
    """Captures the session passed to its constructor; async_update is a no-op."""

    last_instance: "_RecordingFoobar2k | None" = None

    def __init__(self, session, host, port, timeout):
        self.session = session
        self.host = host
        self.port = port
        self.timeout_value = timeout
        self.unique_id = f"{host}_{port}"
        _RecordingFoobar2k.last_instance = self

    async def async_update(self):
        return None


def _ban_new_clientsession(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError(
            "aiohttp.ClientSession() was constructed — code should use "
            "homeassistant.helpers.aiohttp_client.async_get_clientsession(hass)"
        )

    monkeypatch.setattr(aiohttp, "ClientSession", _boom)


async def test_api_init_uses_ha_shared_session(monkeypatch):
    _ban_new_clientsession(monkeypatch)
    monkeypatch.setattr(init_module, "Foobar2k", _RecordingFoobar2k)

    hass = HomeAssistant()
    sentinel_session = object()
    hass._test_clientsession = sentinel_session

    device = await init_module.api_init(hass, "10.0.0.1", 8880)

    assert device is not None
    assert device.session is sentinel_session


async def test_config_flow_uses_ha_shared_session(monkeypatch):
    _ban_new_clientsession(monkeypatch)
    monkeypatch.setattr(cf_module, "Foobar2k", _RecordingFoobar2k)

    hass = HomeAssistant()
    sentinel_session = object()
    hass._test_clientsession = sentinel_session

    flow = cf_module.Foobar2kConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user({"host": "10.0.0.2", "port": 8880})

    assert result["type"] == "create_entry"
    assert _RecordingFoobar2k.last_instance.session is sentinel_session
