"""Iteration 1: Foobar2k.list_playlist_items returns a range of tracks
with caller-chosen columns, mapped back as dicts keyed by column."""
from __future__ import annotations

import json

import pytest

from custom_components.foobar2k import foobar2k as fb2k_module
from tests.fake_session import FakeResponse, FakeSession


def _items_body(rows):
    """rows is a list of dicts; produce a beefweb-shaped playlistItems response.

    Caller controls column order via dict insertion order to match the test.
    """
    return json.dumps(
        {
            "playlistItems": {
                "items": [{"columns": list(r.values())} for r in rows],
                "offset": 0,
                "totalCount": len(rows),
            }
        }
    )


async def test_list_playlist_items_returns_dict_per_row():
    columns = ["%title%", "%artist%", "%album%"]
    session = FakeSession()
    session.queue_get(
        "/api/playlists/pl1/items/0:3",
        FakeResponse(
            body=_items_body(
                [
                    {"title": "A", "artist": "X", "album": "AA"},
                    {"title": "B", "artist": "Y", "album": "BB"},
                    {"title": "C", "artist": "Z", "album": "CC"},
                ]
            )
        ),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    rows = await fb.list_playlist_items("pl1", offset=0, count=3, columns=columns)

    assert rows == [
        {"%title%": "A", "%artist%": "X", "%album%": "AA"},
        {"%title%": "B", "%artist%": "Y", "%album%": "BB"},
        {"%title%": "C", "%artist%": "Z", "%album%": "CC"},
    ]


async def test_list_playlist_items_sends_requested_columns_in_request_body():
    """The columns argument must reach beefweb as the `columns` field of the
    JSON body of the GET (beefweb's convention)."""
    columns = ["%title%", "%path%"]
    session = FakeSession()
    session.queue_get(
        "/api/playlists/pl1/items/5:2",
        FakeResponse(body=_items_body([{"t": "x", "p": "C:/x"}, {"t": "y", "p": "C:/y"}])),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    await fb.list_playlist_items("pl1", offset=5, count=2, columns=columns)

    req = session.requests[-1]
    body = json.loads(req["kwargs"]["data"])
    assert body == {"columns": columns}


async def test_list_playlist_items_returns_empty_list_when_response_missing():
    """Network failure / 5xx → prep_fetch returns None. Must not crash."""
    session = FakeSession()
    session.queue_get(
        "/api/playlists/pl1/items/0:1",
        FakeResponse(status=500, body=""),
    )

    fb = fb2k_module.Foobar2k(session, "host", 8880, 60)
    fb._power = fb2k_module.POWER_ON

    rows = await fb.list_playlist_items("pl1", offset=0, count=1, columns=["%title%"])
    assert rows == []
