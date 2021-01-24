import asyncio
import logging
import re

from homeassistant.core import HomeAssistant
from smartbox import Session, SocketSession

_LOGGER = logging.getLogger(__name__)

_PATH_RE = re.compile(r'^/([^/]+)/(\d+)/([^/]+)')


async def get_devices(hass: HomeAssistant, api_name, basic_auth_creds, username, password):
    session = await hass.async_add_executor_job(Session, api_name, basic_auth_creds, username, password)
    session_devices = await hass.async_add_executor_job(session.get_devices)
    # TODO: gather?
    devices = [
        await create_smartbox_device(hass, session_device['dev_id'], session) for session_device in session_devices
    ]
    return devices


async def create_smartbox_device(hass, dev_id, session):
    '''Factory function for SmartboxDevices'''
    device = SmartboxDevice(dev_id, session)
    await device.initialise_nodes(hass)
    return device


class SmartboxDevice(object):
    def __init__(self, dev_id, session):
        self._dev_id = dev_id
        self._session = session

    async def initialise_nodes(self, hass):
        # Would do in __init__, but needs to be a coroutine
        session_nodes = await hass.async_add_executor_job(self._session.get_nodes, self.dev_id)
        self._nodes = {}
        for node_info in session_nodes:
            status = await hass.async_add_executor_job(self._session.get_status, self._dev_id, node_info)
            node = SmartboxNode(self, node_info, self._session, status)
            self._nodes[(node.node_type, node.addr)] = node

        _LOGGER.debug(f"Creating SocketSession for device {self._dev_id}")
        self._socket_session = SocketSession(self._session, self._dev_id, lambda data: self._on_dev_data(data),
                                             lambda data: self._on_node_update(data))

        _LOGGER.debug(f"Starting SocketSession task for device {self._dev_id}")
        asyncio.create_task(self._socket_session.run())

    def _on_dev_data(self, data):
        _LOGGER.debug(f"Received dev_data: {data}")

    def _on_node_update(self, data):
        _LOGGER.debug(f"Received update: {data}")
        m = _PATH_RE.match(data['path'])
        if not m:
            _LOGGER.error(f"Couldn't match path {data['path']}")
            return
        node_type = m.group(1)
        addr = int(m.group(2))
        update_type = m.group(3)

        if update_type == 'status':
            node_status = data['body']
            node = self._nodes.get((node_type, addr), None)
            if node is None:
                _LOGGER.error(f"Received update for unknown node {node_type} {addr}")
                return
            node.update_status(node_status)
        else:
            _LOGGER.warning(f"Received unknown update type {update_type}: {data}")

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

    @property
    def node_id(self):
        return f"{self._device.dev_id}-{self._node_info['addr']}"

    @property
    def name(self):
        return self._node_info['name']

    @property
    def node_type(self):
        '''Return node type, e.g. 'htr' for heaters'''
        return self._node_info['type']

    @property
    def addr(self):
        return self._node_info['addr']

    @property
    def status(self):
        return self._status

    def update_status(self, status):
        _LOGGER.debug(f"Updating node {self.name} status: {status}")
        self._status = status

    def set_status(self, **status_args):
        self._session.set_status(self._device.dev_id, self._node_info, status_args)

    async def async_update(self, hass):
        _LOGGER.debug("Smartbox node async_update")
