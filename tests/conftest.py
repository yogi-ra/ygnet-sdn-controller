import pytest
from unittest.mock import MagicMock
from netmiko import ConnectHandler # Import ConnectHandler to patch it
from concurrent.futures import Future # Import Future

@pytest.fixture(scope="function")
def mock_netmiko_instance_factory():
    """
    Fixture factory to provide a mocked Netmiko ConnectHandler instance for a specific device_type.
    """
    def _factory(device_type="cisco_ios"):
        mock = MagicMock()
        mock.send_command.return_value = "mocked command output"
        mock.send_multiline.return_value = "mocked multiline command output"
        mock.find_prompt.return_value = "#"
        mock.enable.return_value = None
        mock.device_type = device_type # Set the device_type on the mock
        return mock
    return _factory

@pytest.fixture(autouse=True)
def mock_connection_manager_class(mocker, mock_netmiko_instance_factory):
    """
    Fixture to mock the ConnectionManager class methods.
    """
    # Patch the ConnectHandler class as it's imported and used in connection_manager.py
    # It should return a new mock instance based on the device_type passed to it.
    def mock_connect_handler_side_effect(**kwargs):
        return mock_netmiko_instance_factory(kwargs.get("device_type", "cisco_ios"))

    mocker.patch("src.connection_manager.ConnectHandler", side_effect=mock_connect_handler_side_effect)

    # Patch the ConnectionManager.get_connection method (the class method)
    mock_get_connection = mocker.patch("src.connection_manager.ConnectionManager.get_connection")
    # The get_connection method now returns a Future, so we need to mock that
    # Ensure it returns a Future that resolves to a NEW mock Netmiko instance each time
    mock_get_connection.side_effect = lambda device_info: create_future_with_result(mock_netmiko_instance_factory(device_info.device_type))

    # Patch the ConnectionManager.send_command method
    mock_send_command = mocker.patch("src.connection_manager.ConnectionManager.send_command")
    mock_send_command.side_effect = lambda device_info, command, **kwargs: create_future_with_result("mocked command output")

    return {"get_connection": mock_get_connection, "send_command": mock_send_command}

def create_future_with_result(result):
    future = Future()
    future.set_result(result)
    return future
