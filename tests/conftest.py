import sys
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env.test"))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import pytest
from unittest.mock import MagicMock
from concurrent.futures import Future # Import Future
from src.connection_manager import ConnectionManager # Import the actual class

@pytest.fixture(autouse=True)
def mock_connection_manager_instance(mocker):
    """
    Fixture to mock the ConnectionManager instance methods.
    """
    # Ensure a fresh instance of ConnectionManager for each test
    ConnectionManager._instance = None
    ConnectionManager._connections = {}
    ConnectionManager._connection_locks = {}

    # Patch the instance of ConnectionManager
    mock_instance = mocker.patch("src.controllers.base.connection_manager")

    # Mock the get_connection method on the instance
    mock_instance.get_connection.side_effect = lambda *args, **kwargs: create_future_with_result(MagicMock())

    # Mock the send_command method on the instance to properly handle device_info and command parameters
    def mock_send_command(device_info, command, netmiko_device_type=None, **kwargs):
        return create_future_with_result(f"mocked output for {command}")
    
    mock_instance.send_command.side_effect = mock_send_command

    return {"get_connection": mock_instance.get_connection, "send_command": mock_instance.send_command}

def create_future_with_result(result):
    future = Future()
    future.set_result(result)
    return future