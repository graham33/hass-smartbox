import logging
from unittest.mock import (
    MagicMock,
    NonCallableMock,
    patch,
)

from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from custom_components.smartbox.model import (
    create_smartbox_device,
    get_devices,
    SmartboxDevice,
    SmartboxNode,
)

from .mocks import mock_device

_LOGGER = logging.getLogger(__name__)


async def test_create_smartbox_device(hass):
    dev_1_id = "test_device_id_1"
    mock_dev = mock_device(dev_1_id, [])
    mock_session = MagicMock()
    with patch(
        "custom_components.smartbox.model.SmartboxDevice",
        autospec=True,
        return_value=mock_dev,
    ) as device_ctor_mock:
        device = await create_smartbox_device(hass, dev_1_id, mock_session)
        device_ctor_mock.assert_called_with(dev_1_id, mock_session)
        mock_dev.initialise_nodes.assert_awaited_with(hass)
        assert device == mock_dev


async def test_get_devices(hass, mock_smartbox):
    dev_1_id = "test_device_id_1"
    dev_2_id = "test_device_id_2"  # missing
    test_devices = [
        SmartboxDevice(dev, mock_smartbox.session)
        for dev in mock_smartbox.session.get_devices()
    ]
    with patch(
        "custom_components.smartbox.model.create_smartbox_device",
        autospec=True,
        side_effect=test_devices,
    ) as create_smartbox_device_mock:
        # check we called the smartbox API correctly
        devices = await get_devices(
            hass,
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_API_NAME],
            mock_smartbox.config[DOMAIN][CONF_BASIC_AUTH_CREDS],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_USERNAME],
            mock_smartbox.config[DOMAIN][CONF_ACCOUNTS][0][CONF_PASSWORD],
        )

        # check we created the devices
        create_smartbox_device_mock.assert_any_await(
            hass, dev_1_id, mock_smartbox.session
        )
        create_smartbox_device_mock.assert_any_await(
            hass, dev_2_id, mock_smartbox.session
        )
        assert devices == test_devices


async def test_smartbox_device_init(hass, mock_smartbox):
    mock_device = mock_smartbox.get_devices()[0]
    dev_id = mock_device["dev_id"]

    node_sentinel_1 = MagicMock()
    node_sentinel_2 = MagicMock()
    with patch(
        "custom_components.smartbox.model.SmartboxNode",
        side_effect=[node_sentinel_1, node_sentinel_2],
        autospec=True,
    ) as smartbox_node_ctor_mock:
        device = SmartboxDevice(dev_id, mock_smartbox.session)
        assert device.dev_id == dev_id
        await device.initialise_nodes(hass)
        mock_smartbox.session.get_nodes.assert_called_with(dev_id)

        nodes = list(device.get_nodes())
        mock_nodes = mock_smartbox.session.get_nodes(dev_id)
        assert len(nodes) == len(mock_nodes)

        mock_smartbox.session.get_status.assert_any_call(dev_id, mock_nodes[0])
        mock_smartbox.session.get_status.assert_any_call(dev_id, mock_nodes[1])

        smartbox_node_ctor_mock.assert_any_call(
            device,
            mock_nodes[0],
            mock_smartbox.session,
            mock_smartbox.session.get_status(dev_id, mock_nodes[0]),
        )
        smartbox_node_ctor_mock.assert_any_call(
            device,
            mock_nodes[1],
            mock_smartbox.session,
            mock_smartbox.session.get_status(dev_id, mock_nodes[1]),
        )

        assert dev_id in mock_smartbox.sockets


async def test_smartbox_device_on_dev_data(hass):
    dev_id = "test_device_id_1"
    mock_session = MagicMock()
    mock_node_1 = MagicMock()
    mock_node_2 = MagicMock()
    # Simulate initialise_nodes with mock data, make sure nobody calls the real one
    with patch(
        "custom_components.smartbox.model.SmartboxDevice.initialise_nodes",
        new_callable=NonCallableMock,
    ):
        device = SmartboxDevice(dev_id, mock_session)
        device._nodes = {("htr", 1): mock_node_1, ("thm", 2): mock_node_2}

        mock_dev_data = {"away_status": {"away": True}}
        device.on_dev_data(mock_dev_data)
        assert mock_node_1.away
        assert mock_node_2.away

        mock_dev_data = {"away_status": {"away": False}}
        device.on_dev_data(mock_dev_data)
        assert not mock_node_1.away
        assert not mock_node_2.away


async def test_smartbox_device_on_update(hass, caplog):
    dev_id = "test_device_id_1"
    mock_session = MagicMock()
    mock_node_1 = MagicMock()
    mock_node_2 = MagicMock()
    # Simulate initialise_nodes with mock data, make sure nobody calls the real one
    with patch(
        "custom_components.smartbox.model.SmartboxDevice.initialise_nodes",
        new_callable=NonCallableMock,
    ):
        device = SmartboxDevice(dev_id, mock_session)
        device._nodes = {("htr", 1): mock_node_1, ("thm", 2): mock_node_2}

        mock_status = {"foo": "bar"}
        mock_update = {"path": "/htr/1/status", "body": mock_status}
        device.on_update(mock_update)
        mock_node_1.update_status.assert_called_with(mock_status)
        mock_node_2.update_status.assert_not_called()

        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        mock_update = {"path": "/thm/2/status", "body": mock_status}
        device.on_update(mock_update)
        mock_node_2.update_status.assert_called_with(mock_status)
        mock_node_1.update_status.assert_not_called()

        # test unknown node
        mock_node_1.reset_mock()
        mock_node_2.reset_mock()
        mock_update = {"path": "/htr/3/status", "body": mock_status}
        device.on_update(mock_update)
        mock_node_1.update_status.assert_not_called()
        mock_node_2.update_status.assert_not_called()
        assert (
            "custom_components.smartbox.model",
            logging.ERROR,
            "Received update for unknown node htr 3",
        ) in caplog.record_tuples


async def test_smartbox_node(hass):
    dev_id = "test_device_id_1"
    mock_device = MagicMock()
    mock_device.dev_id = dev_id
    node_addr = 3
    node_type = "thm"
    node_name = "Bathroom Thermostat"
    node_info = {"addr": node_addr, "name": node_name, "type": node_type}
    mock_session = MagicMock()
    initial_status = {"mtemp": 21.4, "stemp": 22.5}

    node = SmartboxNode(mock_device, node_info, mock_session, initial_status)
    assert node.node_id == f"{dev_id}-{node_addr}"
    assert node.name == node_name
    assert node.node_type == node_type
    assert node.addr == node_addr

    assert node.status == initial_status
    new_status = {"mtemp": 21.6, "stemp": 22.5}
    node.update_status(new_status)
    assert node.status == new_status

    node.set_status(stemp=23.5)
    mock_session.set_status.assert_called_with(dev_id, node_info, {"stemp": 23.5})

    assert not node.away
    node.away = True
    assert node.away

    # TODO: currently unused
    await node.async_update(hass)
