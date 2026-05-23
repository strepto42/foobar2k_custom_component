"""Iteration 2: Foobar2k filesystem browser methods.

Wrap beefweb's /api/browser/roots and /api/browser/entries so the entity
can build the Library branch of the media browser without parsing beefweb
JSON directly.
"""
from __future__ import annotations

import json
from urllib.parse import urlparse, parse_qs

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


# ---- browser_roots ----------------------------------------------------------


async def test_browser_roots_returns_configured_music_folders():
    session = FakeSession()
    session.queue_get(
        "/api/browser/roots",
        FakeResponse(
            body=json.dumps(
                {
                    "roots": [
                        {"name": "Music", "path": "C:/Music"},
                        {"name": "Podcasts", "path": "D:/Podcasts"},
                    ]
                }
            )
        ),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    roots = await fb.browser_roots()
    assert roots == [
        {"name": "Music", "path": "C:/Music"},
        {"name": "Podcasts", "path": "D:/Podcasts"},
    ]


async def test_browser_roots_empty_on_failure():
    session = FakeSession()
    session.queue_get("/api/browser/roots", FakeResponse(status=500, body=""))
    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON
    assert await fb.browser_roots() == []


# ---- browser_entries --------------------------------------------------------


async def test_browser_entries_passes_path_as_query_param():
    """The path argument must reach beefweb as a `path` query parameter."""
    session = FakeSession()
    # Default response is enough; we don't care about the body for this test.
    session.set_default(FakeResponse(body=json.dumps({"entries": []})))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    await fb.browser_entries("C:/Music/Artist")

    req = session.requests[-1]
    parsed = urlparse(req["url"])
    qs = parse_qs(parsed.query)
    assert parsed.path == "/api/browser/entries"
    assert qs.get("path") == ["C:/Music/Artist"]


async def test_browser_entries_returns_dirs_and_files_distinguishable():
    """Entries must keep enough info that the entity can render folders vs
    playable files (beefweb's "type": "D"/"F")."""
    session = FakeSession()
    body = json.dumps(
        {
            "entries": [
                {
                    "name": "Album A",
                    "path": "C:/Music/Artist/Album A",
                    "type": "D",
                    "size": 0,
                },
                {
                    "name": "01 Song.flac",
                    "path": "C:/Music/Artist/Album A/01 Song.flac",
                    "type": "F",
                    "size": 12345,
                },
            ]
        }
    )
    session.set_default(FakeResponse(body=body))

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    entries = await fb.browser_entries("C:/Music/Artist")

    assert len(entries) == 2
    assert entries[0]["name"] == "Album A"
    assert entries[0]["type"] == "D"
    assert entries[1]["name"] == "01 Song.flac"
    assert entries[1]["type"] == "F"
    # Path must be preserved verbatim — it's what we'll feed into
    # add_to_playlist later.
    assert entries[1]["path"] == "C:/Music/Artist/Album A/01 Song.flac"


async def test_browser_entries_empty_on_failure():
    session = FakeSession()
    session.set_default(FakeResponse(status=500, body=""))
    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON
    assert await fb.browser_entries("C:/whatever") == []
