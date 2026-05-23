"""Support for Foobar2k api provided by beefweb https://github.com/hyperblast/beefweb."""

import logging
from urllib.parse import unquote, urlparse

from homeassistant.components.media_player import BrowseMedia, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaClass,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING, STATE_UNKNOWN
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .foobar2k import PLAYBACK_MODE_DEFAULT, PLAYBACK_MODE_RANDOM

# media_content_id URL scheme used by browse_media + play_media.
#   foobar2k://playlist/<id>           — play playlist from index 0
#   foobar2k://playlist/<id>/<index>   — play specific track in playlist
#   foobar2k://file/<urlencoded-path>  — enqueue file in active playlist, play it
URL_SCHEME = "foobar2k"

_LOGGER = logging.getLogger(__name__)

SUPPORT_FOOBAR_PLAYER = \
    MediaPlayerEntityFeature.NEXT_TRACK | \
    MediaPlayerEntityFeature.PAUSE | \
    MediaPlayerEntityFeature.PLAY | \
    MediaPlayerEntityFeature.BROWSE_MEDIA | \
    MediaPlayerEntityFeature.PLAY_MEDIA | \
    MediaPlayerEntityFeature.PREVIOUS_TRACK | \
    MediaPlayerEntityFeature.SELECT_SOURCE | \
    MediaPlayerEntityFeature.SELECT_SOUND_MODE | \
    MediaPlayerEntityFeature.SHUFFLE_SET | \
    MediaPlayerEntityFeature.STOP | \
    MediaPlayerEntityFeature.VOLUME_MUTE |  \
    MediaPlayerEntityFeature.VOLUME_SET | \
    MediaPlayerEntityFeature.SEEK

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Foobar 2k platform."""
    foobar2k_api = hass.data[DOMAIN].get(entry.entry_id)
    _LOGGER.debug(f"[Media_Player_FB2k] Init {foobar2k_api.host}:{foobar2k_api.port}")

    if foobar2k_api:
        async_add_entities([Foobar2kDevice(foobar2k_api)], update_before_add=True)


class Foobar2kDevice(MediaPlayerEntity):

    def __init__(self, api):
        """Initialize the device."""
        # Include the server's unique_id (host_port) so multiple foobar2000
        # instances don't share a friendly name.
        self._name = f"{DOMAIN}_{api.unique_id}"
        self._state = STATE_UNKNOWN
        self._service = api
        self._title = None
        self._artist = None
        self._album = None
        self._album_art = None
        self._isMuted = False
        self._volume = 0
        self._track_position = None
        self._track_duration = None
        self._shuffle = False
        self._current_playlist = None
        self._current_sound_mode = None
        self._media_path = None
        self._track_position_measured_at = None
        self._playlists = []
        self._sound_mode_list = self._service.playback_modes

    async def async_update(self):
        await self._service.async_update()
        self._isMuted = self._service.isMuted
        self._volume = self._service.volume
        self._shuffle = self._service.isShuffle
        self._playlists = self._service.playlists
        self._current_playlist = self._service.current_playlist
        self._current_sound_mode = self._service.get_playback_mode_description(
            self._service.playback_mode)
        # Always mirror the service's track fields so paused-state position
        # updates land and stopped-state clears (None) propagate to the UI.
        self._album_art = self._service.album_art
        self._title = self._service.title
        self._artist = self._service.artist
        self._album = self._service.album
        self._media_path = self._service.media_path
        new_position = self._service.track_position
        if new_position != self._track_position:
            self._track_position_measured_at = dt_util.utcnow()
        self._track_position = new_position
        self._track_duration = self._service.track_duration

    @property
    def unique_id(self) -> str:
        """Return the unqiue id for this foobar server."""
        return f'{self._name}_{self._service.unique_id}'

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        current_state = self._service.state
        if (current_state == STATE_PLAYING or current_state == STATE_PAUSED):
            self._state = current_state
        else:
            self._state = STATE_IDLE
        _LOGGER.debug(f"[Media_Player_FB2k] Current State [{self._state}]")

        return self._state

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        supported_features = SUPPORT_FOOBAR_PLAYER
        return supported_features

    @property
    def shuffle(self):
        """Boolean if shuffling is enabled."""
        return self._shuffle

    @property
    def is_volume_muted(self):
        return self._isMuted

    @property
    def volume_level(self):
        """Volume level of the media player (0 to 1)."""
        return self._volume

    @property
    def media_title(self):
        """Title of current playing track."""
        return self._title

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    @property
    def media_artist(self):
        """Artist of current playing track."""
        return self._artist

    @property
    def media_album_name(self):
        """Album name of current playing track."""
        return self._album

    @property
    def media_duration(self):
        """Return the duration of current playing media in seconds."""
        _LOGGER.debug(f"[Media_Player_FB2K] media_duration Called [{self._track_duration}]")
        return self._track_duration

    @property
    def media_position(self):
        """Return the position of current playing media in seconds."""
        _LOGGER.debug(f"[Media_Player_FB2K] media_position Called [{self._track_position}]")
        return self._track_position

    @property
    def media_position_updated_at(self):
        """When the value of media_position was last measured."""
        if self.state in (STATE_PLAYING, STATE_PAUSED):
            return self._track_position_measured_at
        return None

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._album_art

    @property
    def source(self):
        """Return  current source name."""
        return self._current_playlist

    @property
    def media_content_id(self):
        """Return current song full file path"""
        return self._media_path

    @property
    def source_list(self):
        """List of available input sources."""
        _LOGGER.debug("[Media_Player_FB2K] Property Source_List")
        if (self._playlists == {} or self._playlists == []):
            return ["Empty"]
        else:
            return list(self._playlists.keys())

    @property
    def sound_mode(self):
        return self._current_sound_mode

    @property
    def sound_mode_list(self):
        return self._sound_mode_list

    async def async_media_play_pause(self):
        """Send the media player the command for play/pause."""
        _LOGGER.debug("[Media_Player_FB2K] Play / Pause Called")
        await self._service.toggle_play_pause()

    async def async_media_pause(self):
        """Send the media player the command for pause if playing."""
        _LOGGER.debug("[Media_Player_FB2K] Pause Called")
        if (self.state == STATE_PLAYING):
            _LOGGER.debug("[Media_Player_FB2K] Pausing")
            await self._service.pause()

    async def async_media_stop(self):
        """Send the media player the stop command."""
        _LOGGER.debug("[Media_Player_FB2K] Stop Called")
        await self._service.stop()

    async def async_media_play(self):
        """Send the media player the command to play at the current playlist."""
        _LOGGER.debug("[Media_Player_FB2K] Play Called")
        await self._service.play()

    async def async_media_next_track(self):
        """Send the media player the command to play the next song"""
        _LOGGER.debug("[Media_Player_FB2K] Next Track Called")
        await self._service.play_next()

    async def async_media_previous_track(self):
        """Send the media player the command to play the previous song"""
        _LOGGER.debug("[Media_Player_FB2K] Previous Track Called")
        await self._service.play_previous()

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        _LOGGER.debug("[Media_Player_FB2K] Mute Called")
        await self._service.toggle_mute()

    async def async_set_volume_level(self, volume):
        """Send the media player the command for setting the volume (0..1)."""
        _LOGGER.debug(f"[Media_Player_FB2K] set_volume_level Called [{volume}]")
        await self._service.set_volume(volume)

    async def async_media_seek(self, position):
        """Send the media player a command for seeking new position in track."""
        await self._service.set_position(position)

    async def async_set_shuffle(self, shuffle):
        """Send the media player the command for setting the shuffle mode."""
        _LOGGER.debug(f"[Media_Player_FB2K] set_shuffle Called **[{shuffle}]**")
        mode = PLAYBACK_MODE_RANDOM if shuffle else PLAYBACK_MODE_DEFAULT
        await self._service.set_playback_mode(self._service.get_playback_mode_description(mode))

    async def async_select_source(self, source):
        _LOGGER.debug(f"[Media_Player_FB2K] Setting source [{source}]")
        if (source == self._current_playlist):
            return

        playlist_id = self._playlists.get(source)
        await self._service.set_playlist_play(playlist_id, 0)
        self._current_playlist = source

    async def async_select_sound_mode(self, sound_mode):
      """Switch the sound mode of the entity."""
      _LOGGER.debug(f"[Media_Player_FB2K] Sound Mode [{sound_mode}]")
      await self._service.set_playback_mode(sound_mode)

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Return a BrowseMedia tree for the media browser UI.

        Top-level shows two folders (Playlists, Library); drilling into
        Playlists shows each foobar2000 playlist and its tracks. Library
        is built out in a follow-up iteration.
        """
        if not media_content_id:
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id="",
                media_content_type="directory",
                title="foobar2000",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="foobar2k://playlists",
                        media_content_type="directory",
                        title="Playlists",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="foobar2k://library",
                        media_content_type="directory",
                        title="Library",
                        can_play=False,
                        can_expand=True,
                    ),
                ],
            )

        if media_content_id == "foobar2k://playlists":
            children = [
                BrowseMedia(
                    media_class=MediaClass.PLAYLIST,
                    media_content_id=f"foobar2k://playlist/{pid}",
                    media_content_type=MediaType.PLAYLIST,
                    title=title,
                    can_play=True,
                    can_expand=True,
                )
                for title, pid in sorted(self._playlists.items())
            ]
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id="foobar2k://playlists",
                media_content_type="directory",
                title="Playlists",
                can_play=False,
                can_expand=True,
                children=children,
                children_media_class=MediaClass.PLAYLIST,
            )

        parsed = urlparse(media_content_id)
        if parsed.scheme == URL_SCHEME and parsed.netloc == "playlist":
            parts = parsed.path.lstrip("/").split("/")
            if not parts or not parts[0]:
                raise ValueError(f"playlist URL needs an id: {media_content_id!r}")
            playlist_id = parts[0]
            size = await self._service.get_playlist_size(playlist_id)
            rows = await self._service.list_playlist_items(
                playlist_id,
                offset=0,
                count=size,
                columns=["%title%", "%artist%", "%album%"],
            )
            children = [
                BrowseMedia(
                    media_class=MediaClass.TRACK,
                    media_content_id=f"foobar2k://playlist/{playlist_id}/{i}",
                    media_content_type=MediaType.TRACK,
                    title=row.get("%title%") or "(unknown)",
                    can_play=True,
                    can_expand=False,
                )
                for i, row in enumerate(rows)
            ]
            # Reverse-lookup the title for the node label.
            title = next(
                (t for t, pid in self._playlists.items() if pid == playlist_id),
                playlist_id,
            )
            return BrowseMedia(
                media_class=MediaClass.PLAYLIST,
                media_content_id=media_content_id,
                media_content_type=MediaType.PLAYLIST,
                title=title,
                can_play=True,
                can_expand=True,
                children=children,
                children_media_class=MediaClass.TRACK,
            )

        raise ValueError(f"unknown foobar2k:// browse URL: {media_content_id!r}")

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Dispatch a foobar2k:// media URL to the right beefweb call.

        Accepts:
          * foobar2k://playlist/<id>           — play playlist from start
          * foobar2k://playlist/<id>/<index>   — play track at index
        """
        _LOGGER.debug("[Media_Player_FB2K] play_media type=%s id=%s", media_type, media_id)
        parsed = urlparse(media_id)
        if parsed.scheme != URL_SCHEME:
            raise ValueError(
                f"media_id must use the {URL_SCHEME}:// scheme, got {media_id!r}"
            )

        # urlparse of "foobar2k://playlist/pl1/7" gives netloc='playlist',
        # path='/pl1/7'. Strip the leading slash and split.
        parts = parsed.path.lstrip("/").split("/") if parsed.path else []

        if parsed.netloc == "playlist":
            if not parts or not parts[0]:
                raise ValueError(f"playlist URL needs an id: {media_id!r}")
            playlist_id = parts[0]
            index = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            await self._service.set_playlist_play(playlist_id, index)
            return

        if parsed.netloc == "file":
            if not parsed.path or parsed.path == "/":
                raise ValueError(f"file URL needs a path: {media_id!r}")
            path = unquote(parsed.path.lstrip("/"))
            # Enqueue into the active playlist and play the just-added track.
            active_title = self._current_playlist
            if not active_title:
                raise ValueError(
                    "no current playlist — select a source first so file "
                    "playback has somewhere to enqueue to"
                )
            playlist_id = self._playlists.get(active_title)
            if not playlist_id:
                raise ValueError(
                    f"no current playlist id for active source {active_title!r}"
                )
            new_index = await self._service.get_playlist_size(playlist_id)
            await self._service.add_to_playlist(playlist_id, [path])
            await self._service.set_playlist_play(playlist_id, new_index)
            return

        raise ValueError(f"unsupported foobar2k:// URL: {media_id!r}")
