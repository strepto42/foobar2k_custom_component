"""Tests that async methods never call the blocking time.sleep."""
from __future__ import annotations

import json

import pytest

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


_MIN_PLAYER_BODY = json.dumps(
    {
        "player": {
            "playbackState": "playing",
            "playbackMode": 0,
            "activeItem": {},
            "volume": {"isMuted": False, "value": -10, "min": -100},
        }
    }
)


def _fail_if_called(*_a, **_kw):
    raise AssertionError("time.sleep() was called from async code (blocks event loop)")


_EMPTY_PLAYLISTS_BODY = json.dumps({"playlists": []})


def _ready_player(session: FakeSession) -> None:
    """Queue an async_update response + the playlist refresh it triggers
    on state-change (initial 'stopped' → 'playing' in our scripted body)."""
    session.queue_get("/api/player", FakeResponse(body=_MIN_PLAYER_BODY))
    session.queue_get("/api/playlists", FakeResponse(body=_EMPTY_PLAYLISTS_BODY))


async def test_play_next_does_not_call_time_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", _fail_if_called)

    session = FakeSession()
    session.queue_post("/api/player/next", FakeResponse(status=204))
    _ready_player(session)

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = "ON"
    await fb.play_next()


async def test_play_previous_does_not_call_time_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", _fail_if_called)

    session = FakeSession()
    session.queue_post("/api/player/previous", FakeResponse(status=204))
    _ready_player(session)

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = "ON"
    await fb.play_previous()


async def test_set_playlist_play_does_not_call_time_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", _fail_if_called)

    session = FakeSession()
    session.queue_post("/api/player/play/pl1/0", FakeResponse(status=204))
    _ready_player(session)

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = "ON"
    await fb.set_playlist_play("pl1", 0)
