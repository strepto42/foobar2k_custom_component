"""Iteration 4a: async_play_media handles foobar2k://playlist/<id>[/<idx>]
URLs by dispatching to Foobar2k.set_playlist_play."""
from __future__ import annotations

import pytest

from custom_components.foobar2k.media_player import Foobar2kDevice
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from tests.fake_service import FakeService


async def test_play_media_playlist_url_plays_from_start():
    svc = FakeService()
    entity = Foobar2kDevice(svc)

    await entity.async_play_media(
        media_type="playlist",
        media_id="foobar2k://playlist/pl1",
    )

    assert svc.play_calls == [("pl1", 0)]


async def test_play_media_playlist_url_with_index_plays_that_track():
    svc = FakeService()
    entity = Foobar2kDevice(svc)

    await entity.async_play_media(
        media_type="music",
        media_id="foobar2k://playlist/pl1/7",
    )

    assert svc.play_calls == [("pl1", 7)]


async def test_entity_advertises_PLAY_MEDIA_feature():
    """HA only routes media_player.play_media to entities that declare
    the PLAY_MEDIA feature. Without it the service call is a no-op from
    the user's perspective."""
    svc = FakeService()
    entity = Foobar2kDevice(svc)
    assert entity.supported_features & MediaPlayerEntityFeature.PLAY_MEDIA


async def test_play_media_unknown_url_scheme_is_rejected():
    """Unknown URL → ValueError. Better to surface a service-call error in
    HA than to silently do nothing."""
    svc = FakeService()
    entity = Foobar2kDevice(svc)
    with pytest.raises(ValueError):
        await entity.async_play_media(media_type="music", media_id="spotify:track:xxx")
    assert svc.play_calls == []
