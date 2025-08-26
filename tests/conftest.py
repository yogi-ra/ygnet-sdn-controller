import pytest
from unittest.mock import MagicMock
from concurrent.futures import Future # Import Future

@pytest.fixture(autouse=True)
def mock_connection_manager_class(mocker):
    """
    Fixture to mock the ConnectionManager class methods.
    """
    # Patch the ConnectionManager.get_connection method (the class method)
    mock_get_connection = mocker.patch("src.connection_manager.ConnectionManager.get_connection")
    # The get_connection method now returns a Future, so we need to mock that
    # Ensure it returns a Future that resolves to a simple MagicMock
    mock_get_connection.side_effect = lambda device_info, netmiko_device_type: create_future_with_result(MagicMock())

    # Patch the ConnectionManager.send_command method
    mock_send_command = mocker.patch("src.connection_manager.ConnectionManager.send_command")
    mock_send_command.side_effect = lambda device_info, command, netmiko_device_type, **kwargs: create_future_with_result("mocked command output")

    return {"get_connection": mock_get_connection, "send_command": mock_send_command}

def create_future_with_result(result):
    future = Future()
    future.set_result(result)
    return future