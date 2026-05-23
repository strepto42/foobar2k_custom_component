"""Minimal Home Assistant stubs.

The integration imports a handful of HA symbols. We install just enough of them
into sys.modules to make the integration importable in a plain pytest venv —
without pulling in the full homeassistant package or its test harness.

Tests import this module via conftest.py before any custom_components.* import.
"""
from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from enum import IntFlag
from typing import Any


def _make_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def install() -> None:
    if "homeassistant" in sys.modules:
        return

    ha = _make_module("homeassistant")
    ha_const = _make_module("homeassistant.const")
    ha_core = _make_module("homeassistant.core")
    ha_exceptions = _make_module("homeassistant.exceptions")
    ha_config_entries = _make_module("homeassistant.config_entries")
    ha_components = _make_module("homeassistant.components")
    ha_mp = _make_module("homeassistant.components.media_player")
    ha_mp_const = _make_module("homeassistant.components.media_player.const")
    ha_helpers = _make_module("homeassistant.helpers")
    ha_cv = _make_module("homeassistant.helpers.config_validation")
    ha_aiohttp_client = _make_module("homeassistant.helpers.aiohttp_client")
    ha_util = _make_module("homeassistant.util")
    ha_util_dt = _make_module("homeassistant.util.dt")

    # ---- homeassistant.const ----
    ha_const.CONF_HOST = "host"
    ha_const.CONF_NAME = "name"
    ha_const.CONF_PORT = "port"
    ha_const.CONF_TIMEOUT = "timeout"
    ha_const.STATE_OFF = "off"
    ha_const.STATE_ON = "on"
    ha_const.STATE_IDLE = "idle"
    ha_const.STATE_PLAYING = "playing"
    ha_const.STATE_PAUSED = "paused"
    ha_const.STATE_UNKNOWN = "unknown"

    # ---- homeassistant.exceptions ----
    class ConfigEntryNotReady(Exception):
        pass

    ha_exceptions.ConfigEntryNotReady = ConfigEntryNotReady

    # ---- homeassistant.core ----
    class HomeAssistant:
        def __init__(self) -> None:
            self.data: dict[str, Any] = {}
            self.config_entries = _ConfigEntries(self)

    def callback(func):
        return func

    ha_core.HomeAssistant = HomeAssistant
    ha_core.callback = callback

    # ---- homeassistant.config_entries ----
    SOURCE_IMPORT = "import"
    SOURCE_USER = "user"
    CONN_CLASS_LOCAL_POLL = "local_poll"

    class _Flows:
        def __init__(self) -> None:
            self.inits: list[dict] = []

        async def async_init(self, domain, context=None, data=None):
            self.inits.append({"domain": domain, "context": context, "data": data})

    class _ConfigEntries:
        def __init__(self, hass) -> None:
            self._hass = hass
            self.flow = _Flows()
            self._forwarded: list[tuple] = []
            self._unloaded: list[tuple] = []
            self._reloaded: list[str] = []

        async def async_forward_entry_setups(self, entry, platforms):
            self._forwarded.append((entry, tuple(platforms)))
            return True

        async def async_unload_platforms(self, entry, platforms):
            self._unloaded.append((entry, tuple(platforms)))
            return True

        async def async_reload(self, entry_id):
            self._reloaded.append(entry_id)
            return True

    class ConfigEntry:
        def __init__(self, *, data=None, options=None, entry_id="test_entry") -> None:
            self.data = data or {}
            self.options = options or {}
            self.entry_id = entry_id
            self._listeners: list = []

        def add_update_listener(self, listener):
            self._listeners.append(listener)
            return lambda: self._listeners.remove(listener)

    class FlowResultType:
        FORM = "form"
        CREATE_ENTRY = "create_entry"
        ABORT = "abort"

    class _FlowHandlers:
        def __init__(self) -> None:
            self._registry: dict[str, type] = {}

        def register(self, domain):
            def deco(cls):
                self._registry[domain] = cls
                return cls

            return deco

    HANDLERS = _FlowHandlers()

    class ConfigFlow:
        _unique_ids_in_use: set[str] = set()

        def __init_subclass__(cls, *, domain=None, **kwargs) -> None:
            super().__init_subclass__(**kwargs)
            cls._domain = domain

        def __init__(self) -> None:
            self.unique_id: str | None = None
            self.hass: Any = None  # set by HA at runtime; tests assign as needed

        async def async_set_unique_id(self, unique_id):
            self.unique_id = unique_id
            return None

        def _abort_if_unique_id_configured(self):
            if self.unique_id in ConfigFlow._unique_ids_in_use:
                raise _AbortFlow("already_configured")

        def async_show_form(self, *, step_id, data_schema=None, errors=None):
            return {
                "type": FlowResultType.FORM,
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

        def async_create_entry(self, *, title, data):
            if self.unique_id is not None:
                ConfigFlow._unique_ids_in_use.add(self.unique_id)
            return {
                "type": FlowResultType.CREATE_ENTRY,
                "title": title,
                "data": data,
                "unique_id": self.unique_id,
            }

        def async_abort(self, *, reason):
            return {"type": FlowResultType.ABORT, "reason": reason}

    class _AbortFlow(Exception):
        def __init__(self, reason):
            self.reason = reason

    ha_config_entries.SOURCE_IMPORT = SOURCE_IMPORT
    ha_config_entries.SOURCE_USER = SOURCE_USER
    ha_config_entries.CONN_CLASS_LOCAL_POLL = CONN_CLASS_LOCAL_POLL
    ha_config_entries.ConfigEntry = ConfigEntry
    ha_config_entries.ConfigFlow = ConfigFlow
    ha_config_entries.HANDLERS = HANDLERS
    ha_config_entries.FlowResultType = FlowResultType
    ha_config_entries.AbortFlow = _AbortFlow

    # ---- homeassistant.components.media_player ----
    class MediaPlayerEntity:
        pass

    ha_mp.MediaPlayerEntity = MediaPlayerEntity

    class MediaPlayerEntityFeature(IntFlag):
        PAUSE = 1
        SEEK = 2
        VOLUME_SET = 4
        VOLUME_MUTE = 8
        PREVIOUS_TRACK = 16
        NEXT_TRACK = 32
        STOP = 64
        PLAY = 128
        SELECT_SOURCE = 256
        SELECT_SOUND_MODE = 512
        SHUFFLE_SET = 1024
        PLAY_MEDIA = 2048
        BROWSE_MEDIA = 4096

    class MediaType:
        MUSIC = "music"
        TRACK = "track"
        PLAYLIST = "playlist"
        DIRECTORY = "directory"

    class MediaClass:
        DIRECTORY = "directory"
        PLAYLIST = "playlist"
        TRACK = "track"
        MUSIC = "music"
        APP = "app"

    class BrowseMedia:
        """Minimal stand-in for homeassistant.components.media_player.BrowseMedia."""

        def __init__(
            self,
            *,
            media_class,
            media_content_id,
            media_content_type,
            title,
            can_play,
            can_expand,
            children=None,
            thumbnail=None,
            children_media_class=None,
        ):
            self.media_class = media_class
            self.media_content_id = media_content_id
            self.media_content_type = media_content_type
            self.title = title
            self.can_play = can_play
            self.can_expand = can_expand
            self.children = children or []
            self.thumbnail = thumbnail
            self.children_media_class = children_media_class

    ha_mp_const.MediaPlayerEntityFeature = MediaPlayerEntityFeature
    ha_mp_const.MediaType = MediaType
    ha_mp_const.MediaClass = MediaClass
    ha_mp.BrowseMedia = BrowseMedia
    ha_mp_const.ATTR_APP_NAME = "app_name"
    ha_mp_const.ATTR_MEDIA_ALBUM_ARTIST = "media_album_artist"
    ha_mp_const.ATTR_MEDIA_ALBUM_NAME = "media_album_name"
    ha_mp_const.ATTR_MEDIA_DURATION = "media_duration"
    ha_mp_const.ATTR_MEDIA_PLAYLIST = "media_playlist"
    ha_mp_const.ATTR_MEDIA_SHUFFLE = "shuffle"
    ha_mp_const.ATTR_MEDIA_TITLE = "media_title"
    ha_mp_const.ATTR_MEDIA_TRACK = "media_track"
    ha_mp_const.ATTR_MEDIA_VOLUME_MUTED = "is_volume_muted"
    ha_mp_const.ATTR_SOUND_MODE = "sound_mode"
    ha_mp_const.ATTR_SOUND_MODE_LIST = "sound_mode_list"
    ha_mp_const.ATTR_MEDIA_CONTENT_ID = "media_content_id"

    # ---- homeassistant.helpers.config_validation ----
    # Nothing of substance imported by name today; expose attribute lookups so
    # `cv.X` does not blow up.
    def _cv_passthrough(value):
        return value

    ha_cv.__getattr__ = lambda name: _cv_passthrough  # type: ignore[attr-defined]

    # ---- homeassistant.helpers.aiohttp_client ----
    # Tests will override this to hand back a mock session.
    def async_get_clientsession(hass):
        return getattr(hass, "_test_clientsession", None)

    ha_aiohttp_client.async_get_clientsession = async_get_clientsession

    # ---- homeassistant.util ----
    class Throttle:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, func):
            return func

    ha_util.Throttle = Throttle

    # ---- homeassistant.util.dt ----
    _frozen_now: list[datetime] = []

    def utcnow():
        if _frozen_now:
            return _frozen_now[-1]
        return datetime.now(timezone.utc)

    def _freeze(dt):
        _frozen_now.append(dt)

    def _unfreeze():
        if _frozen_now:
            _frozen_now.pop()

    ha_util_dt.utcnow = utcnow
    ha_util_dt._freeze = _freeze
    ha_util_dt._unfreeze = _unfreeze
