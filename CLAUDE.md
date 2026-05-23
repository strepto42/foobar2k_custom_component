# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Home Assistant **custom integration** (HACS-installable) that exposes a foobar2000 instance as a `media_player` entity. It talks to foobar2000 over HTTP using the [beefweb](https://github.com/hyperblast/beefweb) REST API plugin — foobar2000 itself must have beefweb installed and listening (default port 8880).

The shippable code lives entirely under [custom_components/foobar2k/](custom_components/foobar2k/). The repo root contains HACS/install metadata, not source.

## Architecture

Three layers, in order of distance from Home Assistant:

1. **[foobar2k.py](custom_components/foobar2k/foobar2k.py)** — the `Foobar2k` class. Pure beefweb HTTP client (aiohttp). Holds all player state (title, artist, volume, playlists, playback mode, etc.) and exposes async methods (`play`, `pause`, `set_volume`, `set_playlist_play`, `set_playback_mode`, …). Knows nothing about Home Assistant. Endpoints and playback-mode constants are defined at the top of the file.
2. **[media_player.py](custom_components/foobar2k/media_player.py)** — the `Foobar2kDevice(MediaPlayerEntity)` wrapper. Translates HA's `MediaPlayerEntity` contract onto the `Foobar2k` client. **Playlists are exposed as HA "sources"**; **beefweb playback modes are exposed as HA "sound modes"** (this is the non-obvious mapping — there's no concept of audio sound modes here).
3. **[__init__.py](custom_components/foobar2k/__init__.py)** + **[config_flow.py](custom_components/foobar2k/config_flow.py)** — HA integration boilerplate. `async_setup_entry` builds the `Foobar2k` client, stashes it in `hass.data[DOMAIN][entry_id]`, then forwards to the `media_player` platform. Config flow is UI-only (host + optional port).

State flow: HA polls `async_update()` on the entity → entity calls `Foobar2k.async_update()` → that hits `GET /api/player` → response parsed in `set_properties()` → if `playbackState` changed, refresh playlists too → entity copies fields off the client into its own attributes.

### Volume quirk

beefweb reports volume as a negative dB value with a configurable minimum (e.g. `-100` to `0`). The `Foobar2k.volume` property normalizes to `0..(abs(min_volume))` by adding `abs(min_volume)`, and `set_volume` reverses it. `MediaPlayerEntity.volume_level` then divides by 100 to fit HA's 0–1 contract. If you touch volume code, keep all three layers in sync.

### Import style

Both `media_player.py` and `config_flow.py` import the `Foobar2k` client via the absolute path `from custom_components.foobar2k.foobar2k import ...` rather than a relative `from .foobar2k import ...`. This is unusual but intentional in the existing code; matches whatever pattern the rest of the file uses when editing.

## Versioning & release

Bump `version` in [custom_components/foobar2k/manifest.json](custom_components/foobar2k/manifest.json) for every user-visible change — HACS uses it to detect updates. Recent commits follow the form `1.0.2 bug fix`.

There is no build, lint, or test setup in this repo. Validation = install into a running Home Assistant (HACS custom repo, or copy `custom_components/foobar2k/` into `config/custom_components/`) and watch the HA logs (`_LOGGER.debug` calls are dense throughout — enable debug logging for the `foobar2k` logger).

## Out of scope

`quirks/` and `temp_tuya.ts` at the repo root are unrelated scratch files (ZHA Zigbee quirks, Tuya experiments) — they are not part of the integration and should not be touched when working on foobar2k.
