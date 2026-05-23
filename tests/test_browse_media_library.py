"""Iteration 6: async_browse_media — Library branch.

Tree under foobar2k://library:
    Library
    ├── <root name>   (foobar2k://library/<urlencoded-root-path>)
    │   ├── <subdir>  (foobar2k://library/<urlencoded-subdir-path>)
    │   └── <file>    (foobar2k://file/<urlencoded-file-path>)  ← playable
    └── ...
"""
from __future__ import annotations

from urllib.parse import quote

from custom_components.foobar2k.media_player import Foobar2kDevice
from tests.fake_service import FakeService


def _entity_with_library(roots, entries_by_path):
    svc = FakeService()
    svc.roots = roots
    svc.entries = entries_by_path
    entity = Foobar2kDevice(svc)
    return entity, svc


# ---- Library root listing -------------------------------------------------


async def test_library_root_lists_each_music_folder():
    entity, _ = _entity_with_library(
        roots=[
            {"name": "Music", "path": "C:/Music"},
            {"name": "Podcasts", "path": "D:/Podcasts"},
        ],
        entries_by_path={},
    )

    node = await entity.async_browse_media(
        media_content_type="directory",
        media_content_id="foobar2k://library",
    )

    titles = [c.title for c in node.children]
    assert titles == ["Music", "Podcasts"]
    music = node.children[0]
    # Each root is a browsable directory — not directly playable.
    assert music.can_expand is True
    assert music.can_play is False
    # Drill-in URL contains the URL-encoded full path of the root.
    assert music.media_content_id == f"foobar2k://library/{quote('C:/Music', safe='')}"


# ---- Drilling into a folder -----------------------------------------------


async def test_library_folder_lists_subdirs_and_files_with_correct_url_forms():
    music = "C:/Music"
    artist = "C:/Music/Artist"
    album_path = "C:/Music/Artist/Album A"
    song_path = "C:/Music/Artist/Album A/01 Song.flac"

    entity, svc = _entity_with_library(
        roots=[{"name": "Music", "path": music}],
        entries_by_path={
            music: [
                {"name": "Artist", "path": artist, "type": "D", "size": 0},
            ],
            artist: [
                {"name": "Album A", "path": album_path, "type": "D", "size": 0},
                {"name": "Loose Track.flac", "path": "C:/Music/Artist/Loose Track.flac",
                 "type": "F", "size": 4096},
            ],
        },
    )

    node = await entity.async_browse_media(
        media_content_type="directory",
        media_content_id=f"foobar2k://library/{quote(artist, safe='')}",
    )

    titles = [c.title for c in node.children]
    assert titles == ["Album A", "Loose Track.flac"]

    album, track = node.children
    # Folder: browsable, not playable. URL stays under foobar2k://library/.
    assert album.can_expand is True
    assert album.can_play is False
    assert album.media_content_id == f"foobar2k://library/{quote(album_path, safe='')}"

    # File: playable (uses the file: URL form play_media already supports),
    # not expandable.
    assert track.can_expand is False
    assert track.can_play is True
    assert track.media_content_id == (
        f"foobar2k://file/{quote('C:/Music/Artist/Loose Track.flac', safe='')}"
    )


async def test_library_folder_with_no_entries_returns_empty_children():
    entity, _ = _entity_with_library(
        roots=[{"name": "Music", "path": "C:/Music"}],
        entries_by_path={"C:/Empty": []},
    )
    node = await entity.async_browse_media(
        media_content_type="directory",
        media_content_id=f"foobar2k://library/{quote('C:/Empty', safe='')}",
    )
    assert node.children == []


async def test_library_folder_passes_decoded_path_to_browser_entries():
    """URL-encoded path with spaces and drive letters must be decoded
    before it goes to beefweb's browser_entries."""
    path = "C:/My Music/Some Artist"
    entity, svc = _entity_with_library(
        roots=[{"name": "Music", "path": "C:/My Music"}],
        entries_by_path={path: []},
    )

    await entity.async_browse_media(
        media_content_type="directory",
        media_content_id=f"foobar2k://library/{quote(path, safe='')}",
    )

    entries_calls = [c for c in svc.call_log if c[0] == "browser_entries"]
    assert entries_calls == [("browser_entries", (path,))]
