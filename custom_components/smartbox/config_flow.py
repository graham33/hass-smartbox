"""Config flow for Smartbox integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN  # pylint:disable=unused-import

import smartbox

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({("api_name"): str, "basic_auth_creds": str, "username": str, "password": str})


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    def _check_input(field):
        if field is None or len(field) < 1:
            raise InvalidConnectionDetails

    _check_input(data.get('api_name'))
    _check_input(data.get('basic_auth_creds'))
    _check_input(data.get('username'))
    _check_input(data.get('password'))

    _LOGGER.debug(f"Attempting to get session with {data}")

    try:
        # If your PyPI package is not built with async, pass your methods
        # to the executor:
        session = await hass.async_add_executor_job(smartbox.Session, data['api_name'], data['basic_auth_creds'],
                                                    data["username"], data["password"])
    except:
        # TODO: improve
        # If you cannot connect:
        # throw CannotConnect
        # If the authentication is wrong:
        # InvalidAuth
        raise InvalidAuth

    devices = session.get_devices()
    _LOGGER.debug(f"Found devices: {devices}")

    # TODO
    if len(devices) > 1:
        _LOGGER.error("Only one device supported")

    # Return info that you want to store in the config entry.
    return {"title": devices[0]['name']}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smartbox."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidConnectionDetails(exceptions.HomeAssistantError):
    """Error to indicate connection details are invalid."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
