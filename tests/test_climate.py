import logging
import pytest

from homeassistant.setup import async_setup_component
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_LOCKED,
    ATTR_TEMPERATURE,
    ENTITY_MATCH_ALL,
    STATE_UNAVAILABLE,
)
from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_HOME,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
)

from custom_components.smartbox.climate import (
    hvac_mode_to_mode,
    mode_to_hvac_mode,
    status_to_hvac_action,
)

from .mocks import (
    convert_temp,
    get_entity,
    get_entity_id,
    get_object_id,
    get_unique_id,
    round_temp,
)

_LOGGER = logging.getLogger(__name__)


def test_mode_to_hvac_mode():
    assert mode_to_hvac_mode("off") == HVAC_MODE_OFF
    assert mode_to_hvac_mode("auto") == HVAC_MODE_AUTO
    assert mode_to_hvac_mode("modified_auto") == HVAC_MODE_AUTO
    assert mode_to_hvac_mode("manual") == HVAC_MODE_HEAT
    with pytest.raises(ValueError):
        mode_to_hvac_mode("blah")


def test_hvac_mode_to_mode():
    assert hvac_mode_to_mode(HVAC_MODE_OFF) == "off"
    assert hvac_mode_to_mode(HVAC_MODE_AUTO) == "auto"
    assert hvac_mode_to_mode(HVAC_MODE_HEAT) == "manual"
    with pytest.raises(ValueError):
        hvac_mode_to_mode("blah")


def test_status_to_hvac_action():
    assert status_to_hvac_action({"active": True}) == CURRENT_HVAC_HEAT
    assert status_to_hvac_action({"active": False}) == CURRENT_HVAC_IDLE
    with pytest.raises(KeyError):
        status_to_hvac_action({})


def _check_state(hass, mock_node_status, state):
    assert state.state == mode_to_hvac_mode(mock_node_status["mode"])
    assert state.attributes[ATTR_LOCKED] == mock_node_status["locked"]

    assert round_temp(hass, state.attributes[ATTR_CURRENT_TEMPERATURE]) == round_temp(
        hass, convert_temp(hass, mock_node_status["units"], mock_node_status["mtemp"])
    )
    # ATTR_TEMPERATURE actually stores the target temperature
    assert round_temp(hass, state.attributes[ATTR_TEMPERATURE]) == round_temp(
        hass, convert_temp(hass, mock_node_status["units"], mock_node_status["stemp"])
    )

    assert state.attributes[ATTR_HVAC_ACTION] == status_to_hvac_action(mock_node_status)


async def test_basic(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)

            state = hass.states.get(entity_id)

            # check basic properties
            assert state.object_id.startswith(get_object_id(mock_node))
            assert state.entity_id.startswith(get_entity_id(mock_node, CLIMATE_DOMAIN))
            assert state.name == mock_node["name"]
            assert state.attributes[ATTR_FRIENDLY_NAME] == mock_node["name"]

            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            _check_state(hass, mock_node_status, state)

            # check we opened a socket and the run function was awaited
            socket = mock_smartbox.sockets[mock_device["dev_id"]]
            socket.run.assert_awaited()

            mock_smartbox.generate_socket_status_update(
                mock_device,
                mock_node,
                {"mtemp": mock_node_status["mtemp"] + 1},
            )

            await hass.helpers.entity_component.async_update_entity(entity_id)
            new_state = hass.states.get(entity_id)
            assert (
                new_state.attributes[ATTR_CURRENT_TEMPERATURE]
                != state.attributes[ATTR_CURRENT_TEMPERATURE]
            )
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            _check_state(hass, mock_node_status, new_state)


async def test_unavailable(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)

            state = hass.states.get(entity_id)
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            _check_state(hass, mock_node_status, state)

            mock_smartbox.generate_socket_status_update(
                mock_device, mock_node, {"sync_status": "disconnected"}
            )

            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state == STATE_UNAVAILABLE


async def test_away(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    # test everything is 'home'
    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
            state = hass.states.get(entity_id)
            assert state.attributes[ATTR_PRESET_MODE] == PRESET_HOME

    mock_device_1 = mock_smartbox.session.get_devices()[0]
    mock_smartbox.dev_data_update(mock_device_1, {"away_status": {"away": True}})
    # check all device_1's climate entities are away but device_2's are not
    for mock_node in mock_smartbox.session.get_nodes(mock_device_1["dev_id"]):
        unique_id = get_unique_id(mock_device_1, mock_node, "climate")
        entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
        await hass.helpers.entity_component.async_update_entity(entity_id)
        state = hass.states.get(entity_id)
        assert state.attributes[ATTR_PRESET_MODE] == PRESET_AWAY
    # but all device_2's should still be home
    mock_device_2 = mock_smartbox.session.get_devices()[1]
    for mock_node in mock_smartbox.session.get_nodes(mock_device_2["dev_id"]):
        unique_id = get_unique_id(mock_device_2, mock_node, "climate")
        entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
        await hass.helpers.entity_component.async_update_entity(entity_id)
        state = hass.states.get(entity_id)
        assert state.attributes[ATTR_PRESET_MODE] == PRESET_HOME


async def test_set_hvac_mode(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_HVAC_MODE: HVAC_MODE_AUTO, ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
            state = hass.states.get(entity_id)
            assert state.state == HVAC_MODE_AUTO
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert mock_node_status["mode"] == "auto"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_HVAC_MODE: HVAC_MODE_HEAT, ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state == HVAC_MODE_HEAT
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert mock_node_status["mode"] == "manual"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_HVAC_MODE: HVAC_MODE_OFF, ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.state == HVAC_MODE_OFF
            mock_node_status = mock_smartbox.session.get_status(
                mock_device["dev_id"], mock_node
            )
            assert mock_node_status["mode"] == "off"


async def test_set_target_temp(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)

            state = hass.states.get(entity_id)
            old_target_temp = state.attributes[ATTR_TEMPERATURE]

            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {
                    ATTR_TEMPERATURE: old_target_temp + 1,
                    ATTR_ENTITY_ID: get_entity_id(mock_node, CLIMATE_DOMAIN),
                },
                blocking=True,
            )

            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            new_target_temp = state.attributes[ATTR_TEMPERATURE]
            assert new_target_temp == pytest.approx(old_target_temp + 1)


async def test_hvac_action(hass, mock_smartbox):
    assert await async_setup_component(hass, "smartbox", mock_smartbox.config)
    await hass.async_block_till_done()

    for mock_device in mock_smartbox.session.get_devices():
        for mock_node in mock_smartbox.session.get_nodes(mock_device["dev_id"]):
            unique_id = get_unique_id(mock_device, mock_node, "climate")
            entity_id = get_entity(hass, CLIMATE_DOMAIN, unique_id)

            mock_smartbox.generate_socket_status_update(
                mock_device, mock_node, {"active": False}
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.attributes[ATTR_HVAC_ACTION] == CURRENT_HVAC_IDLE

            mock_smartbox.generate_socket_status_update(
                mock_device, mock_node, {"active": True}
            )
            await hass.helpers.entity_component.async_update_entity(entity_id)
            state = hass.states.get(entity_id)
            assert state.attributes[ATTR_HVAC_ACTION] == CURRENT_HVAC_HEAT
