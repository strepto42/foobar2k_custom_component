"""Iteration 4b (part 1): Foobar2k.get_playlist_size returns totalCount.

Needed by play_media-of-a-file: append the file to the active playlist,
then play it at the index it landed at (which equals the *old* size).
"""
from __future__ import annotations

import json

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


async def test_get_playlist_size_returns_totalCount():
    """beefweb returns totalCount even when count=0 items are requested —
    cheap way to read just the size."""
    session = FakeSession()
    session.queue_get(
        "/api/playlists/pl1/items/0:0",
        FakeResponse(
            body=json.dumps(
                {"playlistItems": {"items": [], "offset": 0, "totalCount": 42}}
            )
        ),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    assert await fb.get_playlist_size("pl1") == 42


async def test_get_playlist_size_returns_zero_on_failure():
    session = FakeSession()
    session.queue_get(
        "/api/playlists/pl1/items/0:0",
        FakeResponse(status=500, body=""),
    )
    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON
    assert await fb.get_playlist_size("pl1") == 0
