"""Fix #9: Foobar2k.set_properties must clear track fields when activeItem
is gone (index -1 or missing playlistId). Otherwise the last-played
artist/title/album/path/art/position/duration persist on the client and
propagate to the entity even after Fix #7 lands."""
from __future__ import annotations

import json

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


def _playing_body(*, title, artist, album, path, position, duration):
    return json.dumps(
        {
            "player": {
                "playbackState": "playing",
                "playbackMode": 0,
                "activeItem": {
                    "playlistId": "pl1",
                    "index": 0,
                    "position": position,
                    "duration": duration,
                },
                "volume": {"isMuted": False, "value": -10, "min": -100},
            }
        }
    )


def _stopped_body():
    """Beefweb's stopped player reports activeItem with index -1."""
    return json.dumps(
        {
            "player": {
                "playbackState": "stopped",
                "playbackMode": 0,
                "activeItem": {"playlistId": "", "index": -1},
                "volume": {"isMuted": False, "value": -10, "min": -100},
            }
        }
    )


def _playlist_item_body(artist, title, album, path):
    return json.dumps(
        {
            "playlistItems": {
                "items": [
                    {"columns": [artist, title, "", album, path]},
                ]
            }
        }
    )


async def test_client_clears_track_fields_when_player_stops():
    session = FakeSession()

    # First poll: a track is playing.
    session.queue_get(
        "/api/player",
        FakeResponse(body=_playing_body(
            title="Song A", artist="Artist A", album="Album A",
            path="C:/song.flac", position=42, duration=180,
        )),
    )
    session.queue_get("/api/playlists", FakeResponse(body=json.dumps({"playlists": []})))
    session.queue_get(
        "/api/playlists/pl1/items/0",
        FakeResponse(body=_playlist_item_body("Artist A", "Song A", "Album A", "C:/song.flac")),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()

    # Sanity: track is loaded.
    assert fb.title == "Song A"
    assert fb.artist == "Artist A"
    assert fb.track_position == 42

    # Second poll: player stopped — no active item.
    session.queue_get("/api/player", FakeResponse(body=_stopped_body()))
    session.queue_get(
        "/api/playlists", FakeResponse(body=json.dumps({"playlists": []}))
    )
    await fb.async_update()

    assert fb.title is None, "title should clear when player stops"
    assert fb.artist is None, "artist should clear when player stops"
    assert fb.album is None, "album should clear when player stops"
    assert fb.media_path is None, "media_path should clear when player stops"
    assert fb.album_art is None, "album_art should clear when player stops"
    assert fb.track_position is None or fb.track_position == 0
    assert fb.track_duration is None or fb.track_duration == 0
