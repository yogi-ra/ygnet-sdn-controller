import sys
sys.path.insert(0, '/home/yogi/random/networking/sdn/ygnet-sdn-controller/src')

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

    # Mock the send_command method on the instance
    mock_instance.send_command.side_effect = lambda *args, **kwargs: create_future_with_result("mocked command output")

    return {"get_connection": mock_instance.get_connection, "send_command": mock_instance.send_command}

def create_future_with_result(result):
    future = Future()
    future.set_result(result)
    return future