import logging
import random
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.helpers import entity_registry
from homeassistant.util.temperature import convert as convert_temperature

from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_DEVICE_IDS,
)

_LOGGER = logging.getLogger(__name__)


def mock_device(dev_id, nodes):
    dev = MagicMock()
    dev.dev_id = dev_id
    dev.get_nodes = MagicMock(return_value=nodes)
    dev.initialise_nodes = AsyncMock()
    return dev


def mock_node(dev_id, addr):
    node = MagicMock()
    node.node_type = "htr"
    node.name = f"node_{addr}"
    node.node_id = f"{dev_id}-{addr}"
    node.status = {
        "mtemp": random.random() * 40,
        "stemp": random.random() * 40,
        "units": random.choice(["C", "F"]),
        "sync_status": "ok",
        "locked": False,
        "active": random.choice([True, False]),
        "power": random.random() * 1000,
        "mode": "auto",
    }
    node.async_update = AsyncMock()
    return node


def get_object_id(mock_node):
    return mock_node["name"].lower().replace(" ", "_")


def get_entity_id(mock_node, domain):
    object_id = get_object_id(mock_node)
    return f"{domain}.{object_id}"


def get_unique_id(mock_device, mock_node, device_type):
    return f"{mock_device['dev_id']}-{mock_node['addr']}_{device_type}"


def get_entity(hass, platform, unique_id):
    er = entity_registry.async_get(hass)
    entity_id = er.async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


class MockSmartbox(object):
    def __init__(self, mock_config, num_nodes=2):
        self.config = mock_config
        assert len(mock_config[DOMAIN][CONF_ACCOUNTS]) == 1
        config_dev_ids = mock_config[DOMAIN][CONF_ACCOUNTS][0][CONF_DEVICE_IDS]
        self._devices = list(map(self._mock_smartbox_device, config_dev_ids))
        self._node_info = {
            device["dev_id"]: [
                self._mock_smartbox_node_info(device["dev_id"], i)
                for i in range(num_nodes)
            ]
            for device in self._devices
        }
        # socket has most up to date status
        self._socket_node_status = {
            device["dev_id"]: [
                self._mock_smartbox_node_status() for i in range(num_nodes)
            ]
            for device in self._devices
        }
        # session status can be stale
        self._session_node_status = self._socket_node_status

        self.session = self._mock_smartbox_session()
        self.sockets = {}

    def _mock_smartbox_device(self, dev_id):
        return {
            "dev_id": dev_id,
        }

    def _mock_smartbox_node_info(self, dev_id, addr):
        return {
            "addr": addr,
            "name": f"Test node {dev_id} {addr}",
            # TODO: other node types
            "type": "htr",
        }

    def _mock_smartbox_node_status(self):
        return {
            "mtemp": random.random() * 40,
            "stemp": random.random() * 40,
            "units": random.choice(["C", "F"]),
            "sync_status": "ok",
            "locked": random.choice([True, False]),
            "active": random.choice([True, False]),
            "power": random.random() * 1000,
            "mode": random.choice(["off", "auto", "manual"]),
        }

    def _mock_smartbox_session(self):
        mock_session = MagicMock()
        mock_session.get_devices.return_value = self._devices

        def get_nodes(dev_id):
            return self._node_info[dev_id]

        mock_session.get_nodes.side_effect = get_nodes

        def get_status(dev_id, node):
            return self._get_session_status(dev_id, node["addr"])

        mock_session.get_status.side_effect = get_status

        def set_status(dev_id, node, status_updates):
            self._socket_node_status[dev_id][node["addr"]].update(status_updates)
            self._session_node_status = self._socket_node_status

        mock_session.set_status = set_status

        return mock_session

    def get_mock_socket(self, session, dev_id, on_dev_data, on_update):
        assert session == self.session
        mock_socket = MagicMock()
        mock_socket.dev_id = dev_id
        mock_socket.on_dev_data = on_dev_data
        mock_socket.on_update = on_update
        mock_socket.run = AsyncMock()
        self.sockets[dev_id] = mock_socket
        return mock_socket

    def get_devices(self):
        return self._devices

    def dev_data_update(self, mock_device, dev_data):
        socket = self.sockets[mock_device["dev_id"]]
        socket.on_dev_data(dev_data)

    def _get_session_status(self, dev_id, addr):
        return self._session_node_status[dev_id][addr]

    def _get_socket_status(self, dev_id, addr):
        return self._socket_node_status[dev_id][addr]

    def generate_socket_status_update(self, mock_device, mock_node, status_updates):
        dev_id = mock_device["dev_id"]
        addr = mock_node["addr"]
        socket = self.sockets[dev_id]
        self._socket_node_status[dev_id][addr].update(status_updates)
        socket.on_update(
            {
                "path": f"/{mock_node['type']}/{mock_node['addr']}/status",
                "body": self._get_socket_status(
                    mock_device["dev_id"], mock_node["addr"]
                ),
            }
        )


def convert_temp(hass, node_units, temp):
    # Temperatures are converted to the units of the HA
    # instance, so do the same for comparison
    unit = TEMP_CELSIUS if node_units == "C" else TEMP_FAHRENHEIT
    return convert_temperature(temp, unit, hass.config.units.temperature_unit)


def round_temp(hass, temp):
    # HA uses different precisions for Fahrenheit (whole
    # integers) vs Celsius (tenths)
    if hass.config.units.temperature_unit == TEMP_CELSIUS:
        return round(temp, 1)
    else:
        return round(temp)
