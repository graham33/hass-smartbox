# hass-smartbox
Home Assistant integration for heating smartboxes.


**Note: this is very much a work in progress**, a lot of functionality is
missing or not fully working!

## Installation
This integration uses the [smartbox] Python module, so make sure to install that
into your Home Assistant python environment first.

Then, install the `custom_components/smartbox` directory in this repo to your
Home Assistant `custom_components` directory. See the [Home Assistant docs] for
details.

## Configuration

See [CHANGELOG.md](./CHANGELOG.md) for release notes.

## TODO
* Packaging (requirements.txt etc.)
* Tests
* CI
* Docs
* Handle presets (e.g. away and eco)
* config_flow (only configured via yaml atm)
* Handle adding and removing entities properly
* Ensure token refresh is working
* Graceful cleanup/shutdown of update task
* Handle node types other than heater

[Home Assistant docs]: https://developers.home-assistant.io/docs/creating_integration_file_structure
[smartbox]: https://github.com/graham33/smartbox
