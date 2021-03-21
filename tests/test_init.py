import logging
from unittest.mock import patch

from homeassistant.setup import async_setup_component

from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_PASSWORD,
    CONF_USERNAME,
    SMARTBOX_DEVICES,
)
from .const import MOCK_CONFIG_1, MOCK_CONFIG_2, MOCK_CONFIG_3
from .mocks import mock_device, mock_node

_LOGGER = logging.getLogger(__name__)


async def test_setup_basic(hass):
    dev_1_id = "test_device_id_1"
    mock_node_1 = mock_node(dev_1_id, 1)
    mock_node_2 = mock_node(dev_1_id, 2)
    mock_dev_1 = mock_device(dev_1_id, [mock_node_1, mock_node_2])

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        return_value=[mock_dev_1],
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", MOCK_CONFIG_1)
        await hass.async_block_till_done()
        get_devices_mock.assert_any_await(
            hass,
            MOCK_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            MOCK_CONFIG_1[DOMAIN][CONF_BASIC_AUTH_CREDS],
            MOCK_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            MOCK_CONFIG_1[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]


async def test_setup_multiple_accounts_and_devices(hass):
    dev_1_id = "test_device_id_1"
    mock_dev_1_node_1 = mock_node(dev_1_id, 1)
    mock_dev_1 = mock_device(dev_1_id, [mock_dev_1_node_1])

    dev_2_1_id = "test_device_id_2_1"
    mock_dev_2_1_node_1 = mock_node(dev_2_1_id, 1)
    mock_dev_2_1 = mock_device(dev_2_1_id, [mock_dev_2_1_node_1])

    dev_2_2_id = "test_device_id_2_2"
    mock_dev_2_2_node_1 = mock_node(dev_2_2_id, 1)
    mock_dev_2_2 = mock_device(dev_2_2_id, [mock_dev_2_2_node_1])

    devs = [[mock_dev_1], [mock_dev_2_1, mock_dev_2_2]]

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        side_effect=devs,
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", MOCK_CONFIG_2)
        # first account
        get_devices_mock.assert_any_await(
            hass,
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            MOCK_CONFIG_2[DOMAIN][CONF_BASIC_AUTH_CREDS],
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
        )
        # second account
        get_devices_mock.assert_any_await(
            hass,
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_API_NAME],
            MOCK_CONFIG_2[DOMAIN][CONF_BASIC_AUTH_CREDS],
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_USERNAME],
            MOCK_CONFIG_2[DOMAIN][CONF_ACCOUNTS][1][CONF_PASSWORD],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_2_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_2_2 in hass.data[DOMAIN][SMARTBOX_DEVICES]


async def test_setup_missing_and_extra_devices(hass, caplog):
    # config specifies devices 1 and 2, but 2 is missing and 3 exists
    dev_1_id = "test_device_id_1"
    mock_node_1 = mock_node(dev_1_id, 1)
    mock_node_2 = mock_node(dev_1_id, 2)
    mock_dev_1 = mock_device(dev_1_id, [mock_node_1, mock_node_2])

    dev_2_id = "test_device_id_2"  # missing

    dev_3_id = "test_device_id_3"
    mock_node_1 = mock_node(dev_3_id, 1)
    mock_dev_3 = mock_device(dev_3_id, [mock_node_1])

    with patch(
        "custom_components.smartbox.get_devices",
        autospec=True,
        return_value=[mock_dev_1, mock_dev_3],
    ) as get_devices_mock:
        assert await async_setup_component(hass, "smartbox", MOCK_CONFIG_3)
        get_devices_mock.assert_any_await(
            hass,
            MOCK_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            MOCK_CONFIG_3[DOMAIN][CONF_BASIC_AUTH_CREDS],
            MOCK_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            MOCK_CONFIG_3[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
        )
    assert mock_dev_1 in hass.data[DOMAIN][SMARTBOX_DEVICES]
    assert mock_dev_3 not in hass.data[DOMAIN][SMARTBOX_DEVICES]

    assert (
        "custom_components.smartbox",
        logging.ERROR,
        f"Configured device {dev_2_id} was not found",
    ) in caplog.record_tuples
    assert (
        "custom_components.smartbox",
        logging.WARNING,
        f"Found device {dev_3_id} which was not configured - ignoring",
    ) in caplog.record_tuples
