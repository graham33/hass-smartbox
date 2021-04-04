# Changelog

## 0.1.0 (alpha)

### Bug Fixes
* Fix status handling on node unavailable

### Features
* Add initial tests, minor refactorings
* Add `requirements.txt`
* Add initial tests using pytest-homeassistant-custom-component
* Reformat with black and add CI check
* Add codecov
* Improve custom component manifest
* Support `modified_auto` mode (mapped to HVAC_MODE_AUTO)

### Breaking Changes
* Upgrade to smartbox 0.1.0
  * The API name parameter must now be `api-foo` where it was previously `foo`
    (to connect to `api-foo.xxxx`). This allows some devices which connect to
    `api.xxx` to work.
* Only add configured devices (previously all were added). Report errors if
  configured devices are missing, warnings if extra devices are found.

## 0.0.4 (alpha)

### Features
* Add power sensor
* Implement away preset
* Update to smartbox 0.0.5

### Bugfixes
* Fix state returned by climate entity
  * This was accidentally overridden to return temp rather than default (HVAC
    mode)
  * This primarily caused the current HVAC mode to not be highlighted in the UI,
    but might also impact automations

## 0.0.3 (alpha)

### Features
* Upgrade to smartbox 0.0.4
* Port to new smartbox SocketSession interface
* Fix requirements ref to use github (thanks to @davefrooney)
* Add note on basic auth credentials

## 0.0.2 (alpha)

### Features
* Fixed packaging and added basic installation docs
* Added configuration docs

## 0.0.1 (alpha)

### Features
* Initial alpha version: climate entities and temperature sensors for heaters
  with asynchronous updates
