# foobar2000 Media Player for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant Python library to control [foobar2000](http://www.foobar2000.org/) media player from within Home Assistant. It relies on [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb).

## Installation

### HACS (Recommended)

This integration is in the HACS default catalog, so no custom repository is needed.

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In the HACS panel, search for "Foobar 2000 Player".
3. Click "Download".
4. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/foobar2k` folder from this repository to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

Configuration is via UI only. Provide the URL and port where Foobar 2000 is running.

### Browsing your music library

The integration exposes Home Assistant's media browser with two top-level branches:

- **Playlists** — every foobar2000 playlist, drillable to individual tracks.
- **Library** — the file-system folders that **beefweb** is configured to expose.

> **Note:** the Library branch reads from beefweb's own "Music Folders" setting, **not** from foobar2000's media library. If Library shows up empty, open beefweb's settings in foobar2000 (`File → Preferences → Tools → beefweb`) and add one or more music folders there. Foobar2000's library configuration has no effect on what beefweb advertises.


* The foobar2k media player should work with any media player front end. It has been tested with the excellent [Minimalistic media card](https://github.com/kalkih/mini-media-player). The settings I use are:
 ```yaml
    - type: custom:mini-media-player
      entity: media_player.my_foobar_server
      volume_stateless: false
      artwork: full-cover-fit
      source: icon
      sound_mode: full
      hide:
         name: true
         icon: true   
         shuffle: false
         sound_mode: false
```

## License

Released under the [MIT License](LICENSE).

## Thank you

Big thanks to `ed0zer-projects` who first created a foobar2000 player for Home Assistant. They used `foo_httpcontrol` but I wanted to go with the REST API as supplied by [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb). In any case I used `ed0zer-projects` implementation as a high level guide. Also thank you `HyperBlast` for the REST Api to foobar2000.
