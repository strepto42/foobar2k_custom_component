"""Smoke test: the integration modules import under our HA stubs."""
from __future__ import annotations


def test_foobar2k_client_imports():
    from custom_components.foobar2k.foobar2k import Foobar2k  # noqa: F401


def test_const_imports():
    from custom_components.foobar2k.const import DEFAULT_PORT, DOMAIN, TIMEOUT

    assert DOMAIN == "foobar2k"
    assert DEFAULT_PORT == 8880
    assert TIMEOUT == 60


def test_media_player_imports():
    from custom_components.foobar2k import media_player  # noqa: F401


def test_config_flow_imports():
    from custom_components.foobar2k import config_flow  # noqa: F401


def test_init_imports():
    from custom_components.foobar2k import __init__ as init_mod  # noqa: F401
