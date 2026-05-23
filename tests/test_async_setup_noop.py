"""Fix #14: the YAML async_setup path is broken (duplicate flow init) and
the integration is UI-only. async_setup should be a no-op."""
from __future__ import annotations

import custom_components.foobar2k as init_module
from homeassistant.core import HomeAssistant


async def test_async_setup_does_not_trigger_flow_inits():
    hass = HomeAssistant()

    ok = await init_module.async_setup(hass, {"foobar2k": {"host": "x"}})

    assert ok is True
    assert hass.config_entries.flow.inits == [], (
        f"async_setup should not start any config-entry flows; "
        f"got {hass.config_entries.flow.inits!r}"
    )


async def test_async_setup_returns_true_when_domain_absent():
    hass = HomeAssistant()
    ok = await init_module.async_setup(hass, {})
    assert ok is True
    assert hass.config_entries.flow.inits == []
