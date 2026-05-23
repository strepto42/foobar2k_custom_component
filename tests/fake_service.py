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
        # Recorded calls — tests assert on these.
        self.play_calls: list[tuple[str, int]] = []  # (playlist_id, index)
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
