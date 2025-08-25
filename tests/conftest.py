import pytest
from unittest.mock import MagicMock
from netmiko import ConnectHandler # Import ConnectHandler to patch it

@pytest.fixture
def mock_connection_manager(mocker):
    """
    Fixture to mock netmiko.ConnectHandler and its instances.
    """
    # Create a mock for the ConnectHandler instance
    mock_netmiko_instance = MagicMock()
    mock_netmiko_instance.send_command.return_value = "mocked command output"
    mock_netmiko_instance.send_multiline.return_value = "mocked multiline command output"
    mock_netmiko_instance.find_prompt.return_value = "#"
    mock_netmiko_instance.enable.return_value = None

    # Patch the ConnectHandler class as it's imported and used in connection_manager.py
    mocker.patch("src.connection_manager.ConnectHandler", return_value=mock_netmiko_instance)

    # Patch the connection_manager.get_connection method (the instance)
    mock_get_connection = mocker.patch("src.connection_manager.connection_manager.get_connection")
    mock_get_connection.return_value = mock_netmiko_instance

    return mock_get_connection