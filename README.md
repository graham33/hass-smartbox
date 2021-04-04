# hass-smartbox ![hassfest](https://github.com/graham33/hass-smartbox/workflows/Validate%20with%20hassfest/badge.svg) [![codecov](https://codecov.io/gh/graham33/hass-smartbox/branch/main/graph/badge.svg?token=F3VFCU9WPA)](https://codecov.io/gh/graham33/hass-smartbox)
Home Assistant integration for heating smartboxes.


**Note: this is very much a work in progress**, a lot of functionality is
missing or not fully working!

## Installation
This integration uses the [smartbox] Python module, so make sure to install that
into your Home Assistant python environment first. If you are using hass.io, the
module should be automatically installed from github via the reference in the
`manifest.json` file.

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
  in the 'Version' menu item in the mobile app/web app. If the host name is of
  the form `api-foo.xxxx` or `api.xxxx` use the values `api-foo` or `api`
  respectively.
* Your username and password used for the mobile app/web app.
* Your smartbox device ID, which is shows as the 'Device ID Code' under My
  Devices in the Home section of the mobile app/web app.
* Basic auth credentials: this is an HTTP Basic Auth credential used to do
  initial authentication with the server. Use the base64 encoded string
  directly. See 'Basic Auth Credential' section below for more details.

It's recommended that you store credentials using the built-in [Home Assistant
secrets management].

### Basic Auth Credential
Initial authentication to the smartbox REST API is protected by HTTP Basic Auth,
in addition to the user's username and password which are then used to obtain an
access token. In order not to undermine the security layer it provides, and also
because it might change over time or vary between implementations, **the token
is not provided here and system owners need to find it themselves**.

See [CHANGELOG.md](./CHANGELOG.md) for release notes.

## TODO
* Tests
* CI
* Docs
* config_flow (only configured via yaml atm)
* Support device grouping
* Handle adding and removing entities properly
* Graceful cleanup/shutdown of update task
* Handle node types other than heater
* Handle other presets/modes (e.g. boost, eco, window)

[Home Assistant docs]: https://developers.home-assistant.io/docs/creating_integration_file_structure
[Home Assistant secrets management]: https://www.home-assistant.io/docs/configuration/secrets/
[smartbox]: https://github.com/graham33/smartbox
