"""async_update() must treat aiohttp connection errors as 'device off'."""
from __future__ import annotations

import asyncio

import aiohttp

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeSession


async def test_async_update_handles_aiohttp_ClientError():
    """Server unreachable → power flips to OFF; async_update returns cleanly.

    Before fix: only `requests.exceptions.RequestException` was caught — but
    the client uses aiohttp, so an aiohttp.ClientError propagated out and
    HA would log a traceback every poll cycle.
    """
    session = FakeSession()
    session.queue_get("/api/player", aiohttp.ClientError("connection refused"))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()

    assert fb._power == fb2k_module.POWER_OFF


async def test_async_update_handles_asyncio_TimeoutError():
    """Slow/hung server → power flips to OFF, no traceback."""
    session = FakeSession()
    session.queue_get("/api/player", asyncio.TimeoutError())

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()

    assert fb._power == fb2k_module.POWER_OFF


async def test_requests_module_is_not_imported():
    """The integration is aiohttp-only; the legacy `import requests` exists
    purely to feed the broken exception clause above. Removing it shrinks
    the dependency surface (HACS users currently need `requests` even
    though it is never used for HTTP)."""
    from custom_components.foobar2k import foobar2k as fb2k
    assert not hasattr(fb2k, "requests"), (
        "`import requests` should be removed once the broken except clause is fixed"
    )
