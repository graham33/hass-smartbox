"""The Smartbox integration."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_DEVICE_IDS,
    CONF_PASSWORD,
    CONF_USERNAME,
    SMARTBOX_DEVICES,
    SMARTBOX_NODES,
)
from .model import get_devices, is_supported_node

_LOGGER = logging.getLogger(__name__)


DEVICE_IDS_SCHEMA = vol.Schema([cv.string])

ACCOUNT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_NAME): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_DEVICE_IDS): DEVICE_IDS_SCHEMA,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCOUNTS): vol.All(cv.ensure_list, [ACCOUNT_SCHEMA]),
                vol.Required(CONF_BASIC_AUTH_CREDS): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["climate", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Smartbox component."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Setting up Smartbox integration")

    accounts_cfg = config[DOMAIN][CONF_ACCOUNTS]
    _LOGGER.debug(f"accounts: {accounts_cfg}")
    basic_auth_creds = config[DOMAIN][CONF_BASIC_AUTH_CREDS]
    _LOGGER.debug(f"basic_auth_creds: {basic_auth_creds}")

    hass.data[DOMAIN][SMARTBOX_DEVICES] = []
    hass.data[DOMAIN][SMARTBOX_NODES] = []

    for account in accounts_cfg:
        devices = await get_devices(
            hass,
            account[CONF_API_NAME],
            basic_auth_creds,
            account[CONF_USERNAME],
            account[CONF_PASSWORD],
        )

        found_dev_ids = frozenset(dev.dev_id for dev in devices)
        for dev_id in found_dev_ids.difference(account[CONF_DEVICE_IDS]):
            _LOGGER.warning(
                f"Found device {dev_id} which was not configured - ignoring"
            )

        for device in devices:
            if device.dev_id in account[CONF_DEVICE_IDS]:
                _LOGGER.info(f"Setting up configured device {device.dev_id}")
                hass.data[DOMAIN][SMARTBOX_DEVICES].append(device)

        setup_dev_ids = frozenset(
            dev.dev_id for dev in hass.data[DOMAIN][SMARTBOX_DEVICES]
        )
        for dev_id in frozenset(account[CONF_DEVICE_IDS]) - setup_dev_ids:
            _LOGGER.error(f"Configured device {dev_id} was not found")

    for device in hass.data[DOMAIN][SMARTBOX_DEVICES]:
        nodes = device.get_nodes()
        _LOGGER.debug(f"Configuring nodes for device {device.dev_id} {nodes}")
        for node in nodes:
            if not is_supported_node(node):
                _LOGGER.error(
                    f'Nodes of type "{node.node_type}" are not yet supported; '
                    "no entities will be created. Please file an issue on GitHub."
                )
        hass.data[DOMAIN][SMARTBOX_NODES].extend(nodes)

    if hass.data[DOMAIN][SMARTBOX_DEVICES]:
        for component in PLATFORMS:
            await hass.helpers.discovery.async_load_platform(
                component, DOMAIN, {}, config
            )

    _LOGGER.debug("Finished setting up Smartbox integration")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Smartbox from a config entry."""
    # TODO: implement
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # TODO: implement
    return False
