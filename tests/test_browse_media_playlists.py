"""Iteration 5: async_browse_media — root and Playlists branch.

Tree shape exercised here:
    (root)
    ├── Playlists  (foobar2k://playlists)
    │   ├── <pl title>  (foobar2k://playlist/<id>)
    │   │   ├── <track 0>  (foobar2k://playlist/<id>/0)
    │   │   └── ...
    │   └── ...
    └── Library    (foobar2k://library)  — populated in iteration 6
"""
from __future__ import annotations

import pytest

from custom_components.foobar2k.media_player import Foobar2kDevice
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from tests.fake_service import FakeService


def _entity_with_playlists(playlists):
    """playlists: dict[title, id]. Also installs track lists for some ids."""
    svc = FakeService(playlists=playlists)
    entity = Foobar2kDevice(svc)
    entity._playlists = playlists  # mirror what async_update would do
    return entity, svc


# ---- entity declares BROWSE_MEDIA ------------------------------------------


async def test_entity_advertises_BROWSE_MEDIA_feature():
    entity, _ = _entity_with_playlists({})
    assert entity.supported_features & MediaPlayerEntityFeature.BROWSE_MEDIA


# ---- root level ------------------------------------------------------------


async def test_browse_root_returns_playlists_and_library_branches():
    entity, _ = _entity_with_playlists({"Morning": "pl_m"})
    root = await entity.async_browse_media()

    # Root is a directory the user can expand but not "play".
    assert root.can_expand is True
    assert root.can_play is False
    titles = [c.title for c in root.children]
    assert "Playlists" in titles
    assert "Library" in titles
    ids = [c.media_content_id for c in root.children]
    assert "foobar2k://playlists" in ids
    assert "foobar2k://library" in ids
    for child in root.children:
        assert child.can_expand is True


# ---- Playlists branch ------------------------------------------------------


async def test_browse_playlists_branch_lists_each_playlist_as_expandable_and_playable():
    entity, _ = _entity_with_playlists(
        {"Morning": "pl_m", "Workout": "pl_w", "Chill": "pl_c"}
    )

    node = await entity.async_browse_media(
        media_content_type="directory",
        media_content_id="foobar2k://playlists",
    )

    # All three playlists appear (order not asserted).
    titles = sorted(c.title for c in node.children)
    assert titles == ["Chill", "Morning", "Workout"]
    by_title = {c.title: c for c in node.children}

    morning = by_title["Morning"]
    assert morning.media_content_id == "foobar2k://playlist/pl_m"
    # Playlists are both browsable (show tracks) and directly playable.
    assert morning.can_expand is True
    assert morning.can_play is True


async def test_browse_playlists_branch_with_no_playlists_returns_empty_children():
    entity, _ = _entity_with_playlists({})
    node = await entity.async_browse_media(
        media_content_type="directory",
        media_content_id="foobar2k://playlists",
    )
    assert node.children == []


# ---- Drill into one playlist ----------------------------------------------


async def test_browse_single_playlist_lists_its_tracks():
    entity, svc = _entity_with_playlists({"Morning": "pl_m"})
    svc.playlist_items["pl_m"] = [
        {"%title%": "Sunrise", "%artist%": "A1", "%album%": "Dawn"},
        {"%title%": "Coffee", "%artist%": "A2", "%album%": "Morning"},
    ]
    svc.playlist_sizes["pl_m"] = 2

    node = await entity.async_browse_media(
        media_content_type="playlist",
        media_content_id="foobar2k://playlist/pl_m",
    )

    assert len(node.children) == 2
    first, second = node.children
    assert first.title == "Sunrise"
    assert first.media_content_id == "foobar2k://playlist/pl_m/0"
    # Tracks play but don't expand.
    assert first.can_play is True
    assert first.can_expand is False
    assert second.media_content_id == "foobar2k://playlist/pl_m/1"


async def test_browse_unknown_url_raises_with_helpful_message():
    entity, _ = _entity_with_playlists({})
    with pytest.raises(ValueError, match="(?i)unknown.*foobar2k"):
        await entity.async_browse_media(
            media_content_type="x",
            media_content_id="foobar2k://nope",
        )
