# Changelog

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
