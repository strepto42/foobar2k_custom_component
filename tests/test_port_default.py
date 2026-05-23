"""Fix #10: CONF_PORT is Optional with no default. When the user leaves the
port field blank in the UI, port arrives as missing/None and the constructed
URL becomes 'http://host:None' which never connects. The config flow must
default to DEFAULT_PORT, and async_setup_entry must too as a safety net."""
from __future__ import annotations

import custom_components.foobar2k as init_module
from custom_components.foobar2k import config_flow as cf_module
from custom_components.foobar2k.const import DEFAULT_PORT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


class _RecordingFoobar2k:
    last_instance = None

    def __init__(self, session, host, port, timeout):
        self.session = session
        self.host = host
        self.port = port
        self.unique_id = f"{host}_{port}"
        _RecordingFoobar2k.last_instance = self

    async def async_update(self):
        return None


async def test_config_flow_creates_entry_with_default_port_when_omitted(monkeypatch):
    monkeypatch.setattr(cf_module, "Foobar2k", _RecordingFoobar2k)

    flow = cf_module.Foobar2kConfigFlow()
    flow.hass = HomeAssistant()

    # User submits only host — no port at all.
    result = await flow.async_step_user({"host": "10.0.0.5"})

    assert result["type"] == "create_entry"
    assert result["data"]["port"] == DEFAULT_PORT
    assert _RecordingFoobar2k.last_instance.port == DEFAULT_PORT


async def test_async_setup_entry_falls_back_to_default_port(monkeypatch):
    """If an older entry was saved without a port, async_setup_entry must
    still build the client on DEFAULT_PORT, not on None."""
    monkeypatch.setattr(init_module, "Foobar2k", _RecordingFoobar2k)

    hass = HomeAssistant()
    hass._test_clientsession = object()
    entry = ConfigEntry(data={"host": "10.0.0.6"})  # legacy: no port key

    ok = await init_module.async_setup_entry(hass, entry)

    assert ok is True
    assert _RecordingFoobar2k.last_instance.port == DEFAULT_PORT
