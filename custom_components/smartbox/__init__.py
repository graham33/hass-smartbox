"""The Smartbox integration."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SMARTBOX_NODES
from .model import get_devices

_LOGGER = logging.getLogger(__name__)

CONF_ACCOUNTS = 'accounts'
CONF_API_NAME = 'api_name'
CONF_BASIC_AUTH_CREDS = 'basic_auth_creds'
CONF_DEVICE_IDS = 'device_ids'
CONF_PASSWORD = 'password'
CONF_USERNAME = 'username'
SMARTBOX_DEVICES = 'smartbox_devices'
SMARTBOX_SESSIONS = 'smartbox_sessions'

DEVICE_IDS_SCHEMA = vol.Schema([cv.string])

ACCOUNT_SCHEMA = vol.Schema({
    vol.Required(CONF_API_NAME): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_DEVICE_IDS): DEVICE_IDS_SCHEMA,
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN:
        vol.Schema({
            vol.Required(CONF_ACCOUNTS): vol.All(cv.ensure_list, [ACCOUNT_SCHEMA]),
            vol.Required(CONF_BASIC_AUTH_CREDS): cv.string
        })
    },
    extra=vol.ALLOW_EXTRA)

PLATFORMS = ["climate", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Smartbox component."""
    hass.data.setdefault(DOMAIN, {})

    accounts_cfg = config[DOMAIN][CONF_ACCOUNTS]
    _LOGGER.debug(f"accounts: {accounts_cfg}")
    basic_auth_creds = config[DOMAIN][CONF_BASIC_AUTH_CREDS]
    _LOGGER.debug(f"basic_auth_creds: {basic_auth_creds}")

    hass.data[DOMAIN][SMARTBOX_DEVICES] = []
    hass.data[DOMAIN][SMARTBOX_NODES] = []

    for account in accounts_cfg:
        devices = await get_devices(hass, account[CONF_API_NAME], basic_auth_creds, account[CONF_USERNAME],
                                    account[CONF_PASSWORD])
        hass.data[DOMAIN][SMARTBOX_DEVICES].extend(devices)

    for device in hass.data[DOMAIN][SMARTBOX_DEVICES]:
        nodes = device.get_nodes()
        hass.data[DOMAIN][SMARTBOX_NODES].extend(nodes)

    if hass.data[DOMAIN][SMARTBOX_DEVICES]:
        for component in PLATFORMS:
            await hass.helpers.discovery.async_load_platform(component, DOMAIN, {}, config)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Smartbox from a config entry."""
    # TODO: implement
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # TODO: implement
    return False
