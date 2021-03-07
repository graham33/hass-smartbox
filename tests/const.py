from custom_components.smartbox.const import (
    DOMAIN,
    CONF_ACCOUNTS,
    CONF_API_NAME,
    CONF_BASIC_AUTH_CREDS,
    CONF_DEVICE_IDS,
    CONF_PASSWORD,
    CONF_USERNAME,
)

MOCK_CONFIG_1 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1"],
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

MOCK_CONFIG_2 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1"],
            },
            {
                CONF_API_NAME: "test_api_name_2",
                CONF_USERNAME: "test_username_2",
                CONF_PASSWORD: "test_password_2",
                CONF_DEVICE_IDS: ["test_device_id_2_1", "test_device_id_2_2"],
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}

MOCK_CONFIG_3 = {
    DOMAIN: {
        CONF_ACCOUNTS: [
            {
                CONF_API_NAME: "test_api_name_1",
                CONF_USERNAME: "test_username_1",
                CONF_PASSWORD: "test_password_1",
                CONF_DEVICE_IDS: ["test_device_id_1", "test_device_id_2"],
            },
        ],
        CONF_BASIC_AUTH_CREDS: "test_basic_auth_creds",
    }
}
