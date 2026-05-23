"""Fix #8: media_position_updated_at must return the measurement timestamp,
not utcnow() each call. The latter prevents HA from interpolating the seek
bar between polls — the bar appears frozen even during playback.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from homeassistant.util import dt as dt_util

from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService


async def test_position_updated_at_is_the_measurement_time_not_now():
    svc = FakeService(state="playing", title="X", track_position=42, track_duration=180)

    measured_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt_util._freeze(measured_at)
    try:
        entity = Foobar2kDevice(svc)
        await entity.async_update()
    finally:
        dt_util._unfreeze()

    # Simulate HA reading the property 5 seconds later, without a new poll.
    later = measured_at + timedelta(seconds=5)
    dt_util._freeze(later)
    try:
        reported = entity.media_position_updated_at
    finally:
        dt_util._unfreeze()

    assert reported == measured_at, (
        f"property returned {reported} but the position was measured at "
        f"{measured_at}; returning utcnow() breaks HA's seek-bar interpolation"
    )
