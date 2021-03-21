import logging

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.components.climate import ClimateEntity
from homeassistant.const import ATTR_LOCKED, ATTR_TEMPERATURE
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_HOME,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)

from .const import DOMAIN, SMARTBOX_NODES

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox climate platform")
    if discovery_info is None:
        return

    async_add_entities(
        [
            SmartboxHeater(node)
            for node in hass.data[DOMAIN][SMARTBOX_NODES]
            if node.node_type == "htr"
        ],
        True,
    )
    _LOGGER.debug("Finished setting up Smartbox climate platform")


def mode_to_hvac_mode(mode):
    if mode == "off":
        return HVAC_MODE_OFF
    elif mode == "manual":
        return HVAC_MODE_HEAT
    elif mode == "auto":
        return HVAC_MODE_AUTO
    elif mode == "modified_auto":
        # This occurs when the temperature is modified while in auto mode.
        # Mapping it to auto seems to make this most sense
        return HVAC_MODE_AUTO
    else:
        _LOGGER.error(f"Unknown smartbox node mode {mode}")
        raise ValueError(f"Unknown smartbox node mode {mode}")


def hvac_mode_to_mode(hvac_mode):
    if hvac_mode == HVAC_MODE_OFF:
        return "off"
    elif hvac_mode == HVAC_MODE_HEAT:
        return "manual"
    elif hvac_mode == HVAC_MODE_AUTO:
        return "auto"
    else:
        raise ValueError(f"Unsupported hvac mode {hvac_mode}")


def status_to_hvac_action(status):
    return CURRENT_HVAC_HEAT if status["active"] else CURRENT_HVAC_IDLE


class SmartboxHeater(ClimateEntity):
    """Smartbox heater climate control"""

    def __init__(self, node):
        """Initialize the sensor."""
        self._node = node
        self._status = {}
        self._available = True
        self._supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
        _LOGGER.debug(f"Created node {self.name} unique_id={self.unique_id}")

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"{self._node.node_id}_climate"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._node.name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        _LOGGER.debug(f"Supported features: {self._supported_features}")
        return self._supported_features

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS if self._status["units"] == "C" else TEMP_FAHRENHEIT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self._status["mtemp"])

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return float(self._status["stemp"])

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._node.set_status(stemp=str(temp), units=self._status["units"])

    @property
    def hvac_action(self):
        """Return current operation ie. heat or idle."""
        action = status_to_hvac_action(self._status)
        _LOGGER.debug(f"Current HVAC action for {self.name}: {action}")
        return action

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        hvac_mode = mode_to_hvac_mode(self._status["mode"])
        _LOGGER.debug(
            f"Returning HVAC mode for {self.name}: {hvac_mode} from mode {self._status['mode']}"
        )
        return hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_AUTO, HVAC_MODE_OFF]
        _LOGGER.debug(f"Returning supported HVAC modes {hvac_modes}")
        return hvac_modes

    def set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        _LOGGER.debug(f"Setting HVAC mode to {hvac_mode}")
        self._node.set_status(mode=hvac_mode_to_mode(hvac_mode))

    @property
    def preset_mode(self):
        preset_mode = PRESET_AWAY if self._node.away else PRESET_HOME
        _LOGGER.debug(f"Returning preset mode for {self.name}: {preset_mode}")
        return preset_mode

    @property
    def preset_modes(self):
        preset_modes = [PRESET_AWAY, PRESET_HOME]
        _LOGGER.debug(f"Returning preset modes for {self.name}: {preset_modes}")
        return preset_modes

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {
            ATTR_LOCKED: self._status["locked"],
        }
        _LOGGER.debug(f"Device state attributes: {attrs}")
        return attrs

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._available

    async def async_update(self):
        _LOGGER.debug("Smartbox climate async_update")
        new_status = await self._node.async_update(self.hass)
        # new_status = self._node.status
        _LOGGER.info(f"NEW STATUS {new_status}")
        if new_status["sync_status"] == "ok":
            # update our status
            self._status = new_status
            self._available = True
        else:
            self._available = False
