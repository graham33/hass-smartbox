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
**Note: currently only YAML-based configuration is supported, the UI-based
config flow is not yet implemented.**

Add a section like the following to your Home Assistant config.yaml:

```
smartbox:
  accounts:
  - api_name: <api name>
    username: <api username>
    password: <api password>
    device_ids:
    - <device id>
  basic_auth_creds: <basic auth credentials>
```

You will need the following items of information:
* The API name for your heater vendor. This is visible in the 'API Host' entry
  in the 'Version' menu item in the mobile app/web app. If the API Host is
  `api-foo.xxxx`, use `foo` as the value for this setting.
* Your username and password used for the mobile app/web app.
* Your smartbox device ID, which is shows as the 'Device ID Code' under My
  Devices in the Home section of the mobile app/web app.
* Basic auth credentials: this is an HTTP Basic Auth credential that the mobile
  app and web app use to do initial authentication with the server. Use the
  base64 encoded string directly.

It's recommended that you store credentials using the built-in [Home Assistant
secrets management].


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
[Home Assistant secrets management]: https://www.home-assistant.io/docs/configuration/secrets/
[smartbox]: https://github.com/graham33/smartbox
