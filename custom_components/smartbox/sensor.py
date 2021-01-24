import logging

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity
from homeassistant.const import ATTR_LOCKED

from .const import DOMAIN, SMARTBOX_NODES

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    _LOGGER.debug("Setting up Smartbox sensor platform")
    if discovery_info is None:
        return

    async_add_entities(
        [TemperatureSensor(node) for node in hass.data[DOMAIN][SMARTBOX_NODES] if node.node_type == 'htr'], True)

    _LOGGER.debug("Finished setting up Smartbox sensor platform")


class TemperatureSensor(Entity):
    """Smartbox heater temperature sensor"""

    device_class = DEVICE_CLASS_TEMPERATURE

    def __init__(self, node):
        """Initialize the sensor."""
        self._node = node
        _LOGGER.debug(f"Created node {self.name} unique_id={self.unique_id}")

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"{self._node.node_id}_temperature"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            ATTR_LOCKED: self._node.status['locked'],
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._node.status['mtemp']

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._node.status['sync_status'] == 'ok'

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS if self._node.status['units'] == 'C' else TEMP_FAHRENHEIT

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._node.name

    async def async_update(self):
        _LOGGER.debug("Smartbox sensor async_update")
        await self._node.async_update(self.hass)


# TODO: power sensor?
