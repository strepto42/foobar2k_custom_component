"""Iteration 3: Foobar2k.add_to_playlist enqueues file paths via
POST /api/playlists/{id}/items/add (the beefweb add endpoint).

This is the client-side primitive. The entity's play_media will use it
to support file-by-path playback in the Library branch.
"""
from __future__ import annotations

import json

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


async def test_add_to_playlist_posts_to_correct_endpoint():
    session = FakeSession()
    session.queue_post(
        "/api/playlists/pl1/items/add", FakeResponse(status=204)
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    await fb.add_to_playlist("pl1", ["C:/a.flac", "C:/b.flac"])

    posts = [r for r in session.requests if r["method"] == "POST"]
    assert len(posts) == 1
    assert posts[0]["path"] == "/api/playlists/pl1/items/add"


async def test_add_to_playlist_sends_items_in_request_body():
    """beefweb expects {'items': [...], 'async': false}. The synchronous
    flag matters: without it, play_media might race with the add."""
    session = FakeSession()
    session.queue_post(
        "/api/playlists/pl1/items/add", FakeResponse(status=204)
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    await fb.add_to_playlist("pl1", ["C:/Music/Song.flac"])

    body = json.loads(session.requests[-1]["kwargs"]["data"])
    assert body["items"] == ["C:/Music/Song.flac"]
    assert body["async"] is False


async def test_add_to_playlist_does_nothing_when_powered_off():
    """Other client methods gate on POWER_ON. Match that behaviour so an
    early call before async_update doesn't blow up."""
    session = FakeSession()
    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    # power left at default POWER_OFF
    await fb.add_to_playlist("pl1", ["C:/x.flac"])
    assert session.requests == []
