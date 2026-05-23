"""Fix #12: entity .name must disambiguate multiple foobar2000 servers.

Today every Foobar2kDevice is named "foobar2k" (the domain). Two
instances collide in the friendly-name UI.
"""
from __future__ import annotations

from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService


async def test_two_instances_have_distinct_names():
    a = Foobar2kDevice(FakeService(unique_id="10_0_0_1_8880"))
    b = Foobar2kDevice(FakeService(unique_id="10_0_0_2_8880"))

    assert a.name != b.name, (
        f"both entities are named {a.name!r} — multiple servers collide in UI"
    )
