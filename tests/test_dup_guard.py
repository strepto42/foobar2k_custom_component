"""Fix #11: a host+port already configured must not be added a second time.

The flow already calls async_set_unique_id, but never follows up with
_abort_if_unique_id_configured — so duplicates slip through.
"""
from __future__ import annotations

from custom_components.foobar2k import config_flow as cf_module
from homeassistant.config_entries import AbortFlow
from homeassistant.core import HomeAssistant


async def _run_step(flow, user_input):
    """Mimic HA's flow manager: turn an AbortFlow raised inside a step into
    the same {'type': 'abort'} dict the framework would return."""
    try:
        return await flow.async_step_user(user_input)
    except AbortFlow as exc:
        return {"type": "abort", "reason": exc.reason}


class _NoopFoobar2k:
    def __init__(self, session, host, port, timeout):
        self.unique_id = f"{host}_{port}"

    async def async_update(self):
        return None


async def test_second_attempt_with_same_host_port_aborts(monkeypatch):
    monkeypatch.setattr(cf_module, "Foobar2k", _NoopFoobar2k)

    hass = HomeAssistant()

    flow1 = cf_module.Foobar2kConfigFlow()
    flow1.hass = hass
    first = await _run_step(flow1, {"host": "1.2.3.4", "port": 8880})
    assert first["type"] == "create_entry"

    flow2 = cf_module.Foobar2kConfigFlow()
    flow2.hass = hass
    second = await _run_step(flow2, {"host": "1.2.3.4", "port": 8880})

    assert second["type"] == "abort", (
        f"second attempt should abort with already_configured, got {second!r}"
    )
    assert second["reason"] == "already_configured"
