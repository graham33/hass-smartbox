"""Constants for the Smartbox integration."""

from datetime import timedelta

DOMAIN = "smartbox"

CONF_ACCOUNTS = "accounts"
CONF_API_NAME = "api_name"
CONF_BASIC_AUTH_CREDS = "basic_auth_creds"
CONF_DEVICE_IDS = "device_ids"
CONF_PASSWORD = "password"
CONF_USERNAME = "username"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

SMARTBOX_DEVICES = "smartbox_devices"
SMARTBOX_NODES = "smartbox_nodes"
SMARTBOX_SESSIONS = "smartbox_sessions"
