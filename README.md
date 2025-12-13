# foobar2000 Media Player for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant Python library to control [foobar2000](http://www.foobar2000.org/) media player from within Home Assistant. It relies on [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb).

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. In the HACS panel, go to "Integrations".
3. Click the three dots in the top right corner and select "Custom repositories".
4. Add the repository URL `https://github.com/strepto42/foobar2k_custom_component` and select "Integration" as the category.
5. Click "Add".
6. Search for "Foobar 2000 Player" and click "Download".
7. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/foobar2k` folder from this repository to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

Configuration is via UI only. Provide the URL and port where Foobar 2000 is running.
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

## Thank you

Big thanks to `ed0zer-projects` who first created a foobar2000 player for Home Assistant. They used `foo_httpcontrol` but I wanted to go with the REST API as supplied by [HyperBlast beefweb web interface for foobar2000](https://github.com/hyperblast/beefweb). In any case I used `ed0zer-projects` implementation as a high level guide. Also thank you `HyperBlast` for the REST Api to foobar2000.
