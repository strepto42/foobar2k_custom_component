"""Tests for proper aiohttp exception handling in config_flow and __init__.

These tests fail when the specific `except` clauses reference undefined names
(NameError → swallowed by the broad `except Exception` fallback).
"""
from __future__ import annotations

import logging

import aiohttp
import pytest

import custom_components.foobar2k as init_module
from custom_components.foobar2k import config_flow as cf_module


class _ExplodingFoobar2k:
    """Drop-in replacement for Foobar2k whose async_update raises a given exc."""

    def __init__(self, session, host, port, timeout, *, exc):
        self.unique_id = f"{host}_{port}"
        self._exc = exc

    async def async_update(self):
        raise self._exc


def _patch_foobar2k(monkeypatch, target_module, exc):
    def factory(session, host, port, timeout):
        return _ExplodingFoobar2k(session, host, port, timeout, exc=exc)

    monkeypatch.setattr(target_module, "Foobar2k", factory)


class _NoopTimeout:
    """Sync ctx-manager replacement for async_timeout.timeout() so these tests
    can exercise the exception-handler clauses without tripping the separate
    `with timeout()` / shadowing bugs covered by Fix #4."""

    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


async def test_config_flow_catches_aiohttp_ClientError_specifically(monkeypatch, caplog):
    """When async_update raises aiohttp.ClientError, the specific except clause
    should fire. Currently it references an unimported `ClientError` → NameError →
    the broad `except Exception` catches that NameError → wrong log message.
    """
    monkeypatch.setattr(cf_module, "timeout", _NoopTimeout)
    _patch_foobar2k(monkeypatch, cf_module, aiohttp.ClientError("boom"))

    caplog.set_level(logging.DEBUG, logger=cf_module._LOGGER.name)

    flow = cf_module.Foobar2kConfigFlow()
    result = await flow.async_step_user({"host": "1.2.3.4", "port": 8880})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "device_fail"}
    # The bug: NameError is swallowed by the broad except → "Unexpected error"
    # appears in the log. After fix: the specific ClientError clause logs
    # "ClientError" and the broad clause is never entered.
    assert "Unexpected error creating device" not in caplog.text, (
        "broad `except Exception` was hit — specific ClientError clause is broken"
    )
    assert "ClientError" in caplog.text


async def test_config_flow_catches_HTTPForbidden_specifically(monkeypatch, caplog):
    """403 from the server should map to errors={'base': 'forbidden'} via the
    specific HTTPForbidden clause. Currently `web_exceptions.HTTPForbidden`
    raises NameError → swallowed by broad except → wrong 'device_fail' error.
    """
    monkeypatch.setattr(cf_module, "timeout", _NoopTimeout)
    forbidden = aiohttp.web_exceptions.HTTPForbidden()
    _patch_foobar2k(monkeypatch, cf_module, forbidden)

    flow = cf_module.Foobar2kConfigFlow()
    result = await flow.async_step_user({"host": "1.2.3.4", "port": 8880})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "forbidden"}


async def test_api_init_raises_ConfigEntryNotReady_on_ClientConnectionError(monkeypatch):
    """When the underlying client can't reach the server, api_init must raise
    ConfigEntryNotReady so HA retries setup. Currently `ClientConnectionError`
    is not imported → NameError → swallowed by `except Exception` → api_init
    silently returns None and HA gives up.
    """
    _patch_foobar2k(
        monkeypatch, init_module, aiohttp.ClientConnectionError("nope")
    )

    from homeassistant.exceptions import ConfigEntryNotReady

    with pytest.raises(ConfigEntryNotReady):
        await init_module.api_init(hass=None, host="1.2.3.4", port=8880)
