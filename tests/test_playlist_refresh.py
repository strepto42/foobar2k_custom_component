"""Fix #18: playlists refresh only on playbackState change. If the user
adds a playlist in foobar2000 while a track keeps playing, HA never
discovers it. Refresh on every poll."""
from __future__ import annotations

import json

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


def _player_body(state="playing"):
    return json.dumps(
        {
            "player": {
                "playbackState": state,
                "playbackMode": 0,
                "activeItem": {"playlistId": "", "index": -1},
                "volume": {"isMuted": False, "value": -10, "min": -100},
            }
        }
    )


def _playlists_body(*titles):
    return json.dumps(
        {
            "playlists": [
                {"id": f"pl{i}", "title": t, "isCurrent": i == 0}
                for i, t in enumerate(titles)
            ]
        }
    )


async def test_playlists_refresh_when_state_unchanged():
    """Two polls in a row with the same 'playing' state. The second poll
    should still pick up new playlists added between them."""
    session = FakeSession()

    # First poll — state goes stopped (init) → playing, so playlists refresh.
    session.queue_get("/api/player", FakeResponse(body=_player_body("playing")))
    session.queue_get("/api/playlists", FakeResponse(body=_playlists_body("Old")))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()
    assert "Old" in fb.playlists

    # Second poll — same state ("playing"), but user added "New" in foobar2000.
    session.queue_get("/api/player", FakeResponse(body=_player_body("playing")))
    session.queue_get(
        "/api/playlists", FakeResponse(body=_playlists_body("Old", "New"))
    )

    await fb.async_update()

    assert "New" in fb.playlists, (
        "set_playlists only fires on state-change; user-added playlists "
        "while playback continues are invisible"
    )
