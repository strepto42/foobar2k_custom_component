"""Fix #7: entity must refresh/clear track metadata in all relevant states.

The current implementation only writes title/artist/album/art/position/duration
when state is PLAYING. That leaves the entity showing the previous track when
the user pauses, stops, or skips to silence.
"""
from __future__ import annotations

from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService


async def test_position_updates_while_paused():
    """Seeking while paused should change media_position on next poll."""
    svc = FakeService(
        state="playing",
        title="Song A",
        artist="Artist",
        album="Album",
        track_position=10,
        track_duration=180,
        media_path="C:/a.flac",
        album_art="http://x/art",
    )
    entity = Foobar2kDevice(svc)
    await entity.async_update()
    assert entity.media_position == 10

    # User seeks while paused; service reports new position.
    svc.state = "paused"
    svc.track_position = 90
    await entity.async_update()

    assert entity.media_position == 90, (
        "paused state should still allow position to refresh — "
        "current code skips the refresh block unless state==PLAYING"
    )
    assert entity.media_title == "Song A"


async def test_track_fields_clear_when_playback_stops():
    """When the underlying service reports no track, entity must not keep
    showing the last-played title/artist/art."""
    svc = FakeService(
        state="playing",
        title="Song A",
        artist="Artist",
        album="Album",
        track_position=10,
        track_duration=180,
        media_path="C:/a.flac",
        album_art="http://x/art",
    )
    entity = Foobar2kDevice(svc)
    await entity.async_update()
    assert entity.media_title == "Song A"

    # Service goes idle / playback stopped — no current track at all.
    svc.state = "stopped"
    svc.title = None
    svc.artist = None
    svc.album = None
    svc.media_path = None
    svc.album_art = None
    svc.track_position = None
    svc.track_duration = None
    await entity.async_update()

    assert entity.media_title is None, (
        "entity still shows old title after playback stopped — stale UI"
    )
    assert entity.media_artist is None
    assert entity.media_album_name is None
    assert entity.media_image_url is None
    assert entity.media_position is None
    assert entity.media_duration is None
