import asyncio
import logging
import re

from homeassistant.core import HomeAssistant
from smartbox import Session, SocketSession

_LOGGER = logging.getLogger(__name__)

_AWAY_STATUS_UPDATE_RE = re.compile(r"^/mgr/away_status")
_NODE_STATUS_UPDATE_RE = re.compile(r"^/([^/]+)/(\d+)/status")
_HEATER_NODE_TYPES = ["htr", "htr_mod"]


def is_heater_node(node):
    return node.node_type in _HEATER_NODE_TYPES


def is_supported_node(node):
    # TODO: add support for 'thm' (thermostat) nodes
    return is_heater_node(node)


async def get_devices(
    hass: HomeAssistant, api_name, basic_auth_creds, username, password
):
    session = await hass.async_add_executor_job(
        Session, api_name, basic_auth_creds, username, password
    )
    session_devices = await hass.async_add_executor_job(session.get_devices)
    # TODO: gather?
    devices = [
        await create_smartbox_device(hass, session_device["dev_id"], session)
        for session_device in session_devices
    ]
    return devices


async def create_smartbox_device(hass, dev_id, session):
    """Factory function for SmartboxDevices"""
    device = SmartboxDevice(dev_id, session)
    await device.initialise_nodes(hass)
    return device


class SmartboxDevice(object):
    def __init__(self, dev_id, session):
        self._dev_id = dev_id
        self._session = session

    async def initialise_nodes(self, hass):
        # Would do in __init__, but needs to be a coroutine
        session_nodes = await hass.async_add_executor_job(
            self._session.get_nodes, self.dev_id
        )
        self._nodes = {}
        for node_info in session_nodes:
            status = await hass.async_add_executor_job(
                self._session.get_status, self._dev_id, node_info
            )
            node = SmartboxNode(self, node_info, self._session, status)
            self._nodes[(node.node_type, node.addr)] = node

        _LOGGER.debug(f"Creating SocketSession for device {self._dev_id}")
        self._socket_session = SocketSession(
            self._session,
            self._dev_id,
            lambda data: self.on_dev_data(data),
            lambda data: self.on_update(data),
        )

        _LOGGER.debug(f"Starting SocketSession task for device {self._dev_id}")
        asyncio.create_task(self._socket_session.run())

    def on_dev_data(self, data):
        _LOGGER.debug(f"Received dev_data: {data}")
        self._away_status_update(data["away_status"])

    def _away_status_update(self, away_status):
        _LOGGER.debug(f"Away status update: {away_status}")
        # update all nodes
        for node in self._nodes.values():
            node.away = away_status["away"]

    def _node_status_update(self, node_type, addr, node_status):
        _LOGGER.debug(f"Node status update: {node_status}")
        node = self._nodes.get((node_type, addr), None)
        if node is not None:
            node.update_status(node_status)
        else:
            _LOGGER.error(f"Received update for unknown node {node_type} {addr}")

    def on_update(self, data):
        _LOGGER.debug(f"Received update: {data}")

        m = _NODE_STATUS_UPDATE_RE.match(data["path"])
        if m:
            self._node_status_update(m.group(1), int(m.group(2)), data["body"])
            return

        m = _AWAY_STATUS_UPDATE_RE.match(data["path"])
        if m:
            self._away_status_update(data["body"])
            return

        _LOGGER.error(f"Couldn't match update {data['path']}")

    @property
    def dev_id(self):
        return self._dev_id

    def get_nodes(self):
        return self._nodes.values()


class SmartboxNode(object):
    def __init__(self, device, node_info, session, status):
        self._device = device
        self._node_info = node_info
        self._session = session
        self._status = status
        self._away = False

    @property
    def node_id(self):
        # TODO: are addrs only unique among node types, or for the whole device?
        return f"{self._device.dev_id}-{self._node_info['addr']}"

    @property
    def name(self):
        return self._node_info["name"]

    @property
    def node_type(self):
        """Return node type, e.g. 'htr' for heaters"""
        return self._node_info["type"]

    @property
    def addr(self):
        return self._node_info["addr"]

    @property
    def status(self):
        return self._status

    def update_status(self, status):
        _LOGGER.debug(f"Updating node {self.name} status: {status}")
        self._status = status

    def set_status(self, **status_args):
        self._session.set_status(self._device.dev_id, self._node_info, status_args)

    @property
    def away(self):
        return self._away

    @away.setter
    def away(self, away):
        _LOGGER.debug(f"Updating node {self.name} away status: {away}")
        self._away = away

    async def async_update(self, hass):
        _LOGGER.debug("Smartbox node async_update")
        return self._status
