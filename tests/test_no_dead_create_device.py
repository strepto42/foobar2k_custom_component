"""Fix #5: the unreachable `create_device` method on the config flow class
contains an `await Foobar2k(...)` against a non-async constructor (TypeError
at call time) plus copies of the Fix #1 / Fix #4 bugs. No code reaches it.

This test asserts the method is gone — if anyone reintroduces it (e.g. by
copy-paste), this fails and forces them to look at why it was removed.
"""
from __future__ import annotations


def test_create_device_is_not_defined_on_config_flow():
    from custom_components.foobar2k.config_flow import Foobar2kConfigFlow

    assert not hasattr(Foobar2kConfigFlow, "create_device"), (
        "create_device was a dead, broken duplicate of async_step_user — "
        "do not reintroduce it; extend async_step_user instead."
    )
