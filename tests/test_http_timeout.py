"""Fix #13: Foobar2k stores self._timeout but never passes it to aiohttp.
A hung foobar2000 server would hang HA polling indefinitely."""
from __future__ import annotations

import json

import aiohttp

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


_PLAYER_BODY = json.dumps(
    {
        "player": {
            "playbackState": "stopped",
            "playbackMode": 0,
            "activeItem": {"playlistId": "", "index": -1},
            "volume": {"isMuted": False, "value": -10, "min": -100},
        }
    }
)


async def test_fetch_get_passes_aiohttp_timeout():
    session = FakeSession()
    session.queue_get("/api/player", FakeResponse(body=_PLAYER_BODY))
    session.queue_get(
        "/api/playlists", FakeResponse(body=json.dumps({"playlists": []}))
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, timeout=7)
    await fb.async_update()

    get_calls = [r for r in session.requests if r["method"] == "GET"]
    assert get_calls, "no GET was made"
    for call in get_calls:
        timeout = call["kwargs"].get("timeout")
        assert isinstance(timeout, aiohttp.ClientTimeout), (
            f"GET {call['path']} was issued without a ClientTimeout"
        )
        assert timeout.total == 7


async def test_fetch_post_passes_aiohttp_timeout():
    session = FakeSession()
    session.queue_post("/api/player/play", FakeResponse(status=204))

    fb = fb2k_module.Foobar2k(session, "host", 8880, timeout=7)
    fb._power = fb2k_module.POWER_ON
    fb._state = fb2k_module.STATE_PAUSED  # ensures we hit POST /play not /play/{}/{}
    await fb.play()

    post_calls = [r for r in session.requests if r["method"] == "POST"]
    assert post_calls
    for call in post_calls:
        timeout = call["kwargs"].get("timeout")
        assert isinstance(timeout, aiohttp.ClientTimeout)
        assert timeout.total == 7
