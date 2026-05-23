"""Fix #19: Foobar2k._power was only set inside async_update. Any read
before the first update (e.g. an early .play() call on misconfigured setup)
raised AttributeError."""
from __future__ import annotations

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeSession


def test_power_attribute_set_before_first_update():
    fb = fb2k_module.Foobar2k(FakeSession(), "host", 8880, 60)
    # No async_update has been called yet.
    assert fb.power == fb2k_module.POWER_OFF
