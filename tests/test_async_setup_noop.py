"""Fix #14: the YAML async_setup path is broken (duplicate flow init) and
the integration is UI-only. Removed entirely — HA's integration loader
treats a missing async_setup as a successful no-op."""
from __future__ import annotations

import custom_components.foobar2k as init_module


def test_async_setup_is_not_defined():
    """Hassfest also warns when async_setup is present without a
    CONFIG_SCHEMA. Removing the no-op satisfies both that warning and the
    'don't launch duplicate flow inits' goal of Fix #14."""
    assert not hasattr(init_module, "async_setup"), (
        "async_setup was the broken YAML import path; it should stay gone"
    )
