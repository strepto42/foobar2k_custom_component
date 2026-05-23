"""Iteration 4b (part 2): async_play_media for foobar2k://file/... URLs.

Expected flow: get current playlist size N → append file via add_to_playlist
→ play that playlist at index N (where the new file just landed)."""
from __future__ import annotations

from urllib.parse import quote

import pytest

from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService


def _entity_with_active_playlist(playlist_title="Default", playlist_id="pl_default",
                                  current_size=10):
    """Build an entity whose current playlist is `playlist_title` and whose
    underlying playlist has `current_size` tracks already in it."""
    svc = FakeService(
        playlists={playlist_title: playlist_id},
        current_playlist=playlist_title,
    )
    svc.playlist_sizes[playlist_id] = current_size
    entity = Foobar2kDevice(svc)
    # Mirror what async_update would normally do — the entity reads its own
    # mirrored copies of playlists / current_playlist.
    entity._playlists = svc.playlists
    entity._current_playlist = svc.current_playlist
    return entity, svc, playlist_id


async def test_play_media_file_url_appends_then_plays_at_new_index():
    entity, svc, pl_id = _entity_with_active_playlist(current_size=10)
    path = "C:/Music/Artist/Album/01 Song.flac"

    await entity.async_play_media(
        media_type="music",
        media_id=f"foobar2k://file/{quote(path, safe='')}",
    )

    # The new file lands at index 10 (the old size).
    assert svc.add_calls == [(pl_id, [path])]
    assert svc.play_calls == [(pl_id, 10)]
    # Ordering matters: size BEFORE add, add BEFORE play.
    op_order = [call[0] for call in svc.call_log]
    assert op_order == ["get_playlist_size", "add_to_playlist", "set_playlist_play"]


async def test_play_media_file_url_decodes_path_with_colons_and_spaces():
    entity, svc, pl_id = _entity_with_active_playlist(current_size=0)
    path = "C:/My Music/Artist Name/Album/01 Track.flac"

    await entity.async_play_media(
        media_type="music",
        media_id=f"foobar2k://file/{quote(path, safe='')}",
    )

    assert svc.add_calls == [(pl_id, [path])]


async def test_play_media_file_url_raises_when_no_current_playlist():
    """Without a current playlist there's nowhere to enqueue. Surface this
    as a service-call error rather than silently dropping the request."""
    svc = FakeService(playlists={}, current_playlist=None)
    entity = Foobar2kDevice(svc)
    entity._playlists = {}
    entity._current_playlist = None

    with pytest.raises(ValueError, match="(?i)no current playlist"):
        await entity.async_play_media(
            media_type="music",
            media_id=f"foobar2k://file/{quote('C:/x.flac', safe='')}",
        )
    assert svc.add_calls == []
    assert svc.play_calls == []
