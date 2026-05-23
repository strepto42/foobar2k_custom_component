"""A tiny fake of Foobar2k that lets media_player tests drive the entity."""
from __future__ import annotations


class FakeService:
    """Mimics the Foobar2k client surface the media_player entity reads."""

    def __init__(self, **overrides):
        self.unique_id = "host_8880"
        self.isMuted = False
        self.volume = 50
        self.isShuffle = False
        self.playlists = {}
        self.current_playlist = None
        self.playback_mode = 0
        self.album_art = None
        self.title = None
        self.artist = None
        self.album = None
        self.media_path = None
        self.track_position = None
        self.track_duration = None
        self.state = "stopped"
        self.update_calls = 0
        # Recorded calls — tests assert on these (and on their ordering).
        self.play_calls: list[tuple[str, int]] = []  # (playlist_id, index)
        self.add_calls: list[tuple[str, list[str]]] = []  # (playlist_id, paths)
        self.call_log: list[tuple[str, tuple]] = []  # ordered cross-method log
        # Tests can override via .playlist_sizes[playlist_id] = N.
        self.playlist_sizes: dict[str, int] = {}
        # playlist_id → list of column-dicts as list_playlist_items returns
        self.playlist_items: dict[str, list[dict]] = {}
        for k, v in overrides.items():
            setattr(self, k, v)

    @property
    def playback_modes(self):
        return ["Default", "Repeat Playlist", "Random"]

    def get_playback_mode_description(self, mode):
        modes = {0: "Default", 1: "Repeat Playlist", 3: "Random"}
        return modes.get(mode, "Default")

    async def async_update(self):
        self.update_calls += 1

    async def set_playlist_play(self, playlist_id, index):
        self.play_calls.append((playlist_id, index))
        self.call_log.append(("set_playlist_play", (playlist_id, index)))

    async def get_playlist_size(self, playlist_id):
        size = self.playlist_sizes.get(playlist_id, 0)
        self.call_log.append(("get_playlist_size", (playlist_id, size)))
        return size

    async def list_playlist_items(self, playlist_id, offset, count, columns):
        rows = self.playlist_items.get(playlist_id, [])
        self.call_log.append(
            ("list_playlist_items", (playlist_id, offset, count, tuple(columns)))
        )
        return rows[offset:offset + count]

    async def add_to_playlist(self, playlist_id, paths):
        paths = list(paths)
        self.add_calls.append((playlist_id, paths))
        self.call_log.append(("add_to_playlist", (playlist_id, paths)))
        # Mimic real beefweb: the playlist grows by len(paths).
        self.playlist_sizes[playlist_id] = (
            self.playlist_sizes.get(playlist_id, 0) + len(paths)
        )
