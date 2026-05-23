"""Fix #15: update_listener is defined at module level but never registered
via entry.add_update_listener. There's also no options flow, so the listener
can never fire. Dead code — remove it."""
from __future__ import annotations

import custom_components.foobar2k as init_module


def test_update_listener_is_not_defined():
    assert not hasattr(init_module, "update_listener"), (
        "update_listener is unreachable: no options flow exists and "
        "async_setup_entry never calls entry.add_update_listener. "
        "Implement an options flow before reintroducing it."
    )
