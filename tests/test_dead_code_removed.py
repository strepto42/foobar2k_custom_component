"""Fix #16: assert deprecated HA patterns and other dead code are gone."""
from __future__ import annotations


def test_config_flow_has_no_CONNECTION_CLASS():
    """CONNECTION_CLASS was removed from HA — replaced by iot_class in
    manifest.json (already set to local_polling)."""
    from custom_components.foobar2k.config_flow import Foobar2kConfigFlow
    assert not hasattr(Foobar2kConfigFlow, "CONNECTION_CLASS")


def test_media_player_has_no_unused_DEFAULT_TIMEOUT():
    """media_player.py defined DEFAULT_TIMEOUT = 2 but never used it."""
    from custom_components.foobar2k import media_player
    assert not hasattr(media_player, "DEFAULT_TIMEOUT")


def test_entity_has_no_should_poll_override():
    """Was commented out — remove instead of carrying a dead block."""
    from custom_components.foobar2k.media_player import Foobar2kDevice
    # Property defined on the subclass would appear in __dict__.
    assert "should_poll" not in Foobar2kDevice.__dict__


def test_entity_has_no_media_playlist_property():
    """Was commented out — remove instead of carrying a dead block."""
    from custom_components.foobar2k.media_player import Foobar2kDevice
    assert "media_playlist" not in Foobar2kDevice.__dict__


def test_init_module_has_no_unused_helpers_in_namespace():
    """Unused imports from old YAML setup path should be gone."""
    import custom_components.foobar2k as init_module
    for name in ("Throttle", "cv", "SOURCE_IMPORT"):
        assert not hasattr(init_module, name), (
            f"{name} is imported but unused in custom_components.foobar2k"
        )
