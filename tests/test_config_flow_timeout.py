"""Fix #4 — the `with timeout(TIMEOUT)` block in config_flow.async_step_user.

Two bugs in the same block:
  * `with timeout(...)` is invalid in async_timeout >=4 (only async-context-manager)
  * `timeout` is shadowed inside the block, so Foobar2k(... timeout) receives
    the async_timeout function instead of the int TIMEOUT.
"""
from __future__ import annotations

from custom_components.foobar2k import config_flow as cf_module


class _RecordingFoobar2k:
    """Captures ctor args; async_update is a no-op."""

    last_instance: "_RecordingFoobar2k | None" = None

    def __init__(self, session, host, port, timeout):
        self.unique_id = f"{host}_{port}"
        self.ctor_args = {
            "session": session,
            "host": host,
            "port": port,
            "timeout": timeout,
        }
        _RecordingFoobar2k.last_instance = self

    async def async_update(self):
        return None


async def test_foobar2k_receives_integer_timeout_not_async_timeout_function(monkeypatch):
    """The `timeout` name inside `with timeout(TIMEOUT):` is the async_timeout
    function, not the integer. Passing it to Foobar2k means client HTTP
    calls (once they actually use _timeout) would receive a function as
    their `total=` value and break at request time."""
    monkeypatch.setattr(cf_module, "Foobar2k", _RecordingFoobar2k)

    flow = cf_module.Foobar2kConfigFlow()
    await flow.async_step_user({"host": "10.0.0.1", "port": 8880})

    inst = _RecordingFoobar2k.last_instance
    assert inst is not None
    assert inst.ctor_args["timeout"] == cf_module.TIMEOUT, (
        f"expected int TIMEOUT, got {type(inst.ctor_args['timeout']).__name__}: "
        f"{inst.ctor_args['timeout']!r}"
    )


async def test_async_step_user_creates_entry_on_success(monkeypatch):
    """End-to-end: timeout block must not raise so the happy path completes.

    Before fix: `with timeout(TIMEOUT)` raises TypeError on async_timeout 4+.
    The broad except clause then masks it as a 'device_fail' form result —
    the user can never successfully configure the integration.
    """
    monkeypatch.setattr(cf_module, "Foobar2k", _RecordingFoobar2k)

    flow = cf_module.Foobar2kConfigFlow()
    result = await flow.async_step_user({"host": "10.0.0.2", "port": 8880})

    assert result["type"] == "create_entry", (
        f"happy path should produce an entry, got {result!r}"
    )
    assert result["data"] == {"host": "10.0.0.2", "port": 8880}
