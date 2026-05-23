"""Fix #20: volume math hard-coded /100. If beefweb's volume range isn't
-100..0, the volume_level property can never reach 1.0 and set_volume
sends out-of-range values to the server.
"""
from __future__ import annotations

import json

from custom_components.foobar2k import foobar2k as fb2k_module
from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService
from tests.fake_session import FakeResponse, FakeSession


def _player_body(*, volume_value, volume_min):
    return json.dumps(
        {
            "player": {
                "playbackState": "stopped",
                "playbackMode": 0,
                "activeItem": {"playlistId": "", "index": -1},
                "volume": {
                    "isMuted": False,
                    "value": volume_value,
                    "min": volume_min,
                },
            }
        }
    )


async def test_volume_at_max_reaches_1_with_nonstandard_min():
    """beefweb configured min = -50; current = 0 dB (max). The entity
    must report volume_level == 1.0, not 0.5."""
    session = FakeSession()
    session.queue_get(
        "/api/player", FakeResponse(body=_player_body(volume_value=0, volume_min=-50))
    )
    session.queue_get("/api/playlists", FakeResponse(body=json.dumps({"playlists": []})))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()

    # We want the client to expose volume as a 0..1 fraction.
    assert fb.volume == 1.0, (
        f"max volume with min=-50 should be 1.0, got {fb.volume}"
    )


async def test_volume_midpoint_with_default_minus100_range():
    session = FakeSession()
    session.queue_get(
        "/api/player",
        FakeResponse(body=_player_body(volume_value=-50, volume_min=-100)),
    )
    session.queue_get("/api/playlists", FakeResponse(body=json.dumps({"playlists": []})))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    await fb.async_update()

    assert fb.volume == 0.5


async def test_set_volume_sends_correct_db_for_nonstandard_range():
    """Asking for 0.5 with min=-50 should POST volume=-25 (dB)."""
    session = FakeSession()
    session.queue_post("/api/player", FakeResponse(status=204))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON
    fb._min_volume = -50
    await fb.set_volume(0.5)

    posts = [r for r in session.requests if r["method"] == "POST"]
    assert posts, "no POST was issued"
    body = json.loads(posts[-1]["kwargs"]["data"])
    assert body == {"volume": -25}


async def test_entity_volume_level_is_pass_through_from_service():
    """The entity must not divide by 100 — that hardcodes the -100..0 range."""
    svc = FakeService(volume=0.5)
    entity = Foobar2kDevice(svc)
    await entity.async_update()
    assert entity.volume_level == 0.5
