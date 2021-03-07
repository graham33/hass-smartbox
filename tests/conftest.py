import pytest
from unittest.mock import patch

from .const import MOCK_CONFIG_3
from .mocks import MockSmartbox

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_smartbox():
    mock_smartbox = MockSmartbox(MOCK_CONFIG_3)

    with patch(
        "custom_components.smartbox.model.Session",
        autospec=True,
        return_value=mock_smartbox.session,
    ):
        with patch(
            "custom_components.smartbox.model.SocketSession",
            autospec=True,
            side_effect=mock_smartbox.get_mock_socket,
        ):
            yield mock_smartbox
