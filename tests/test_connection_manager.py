import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from src.connection_manager import ConnectionManager
from src.device_info import DeviceConnectionInfo

@pytest.fixture
def mock_connect_handler():
    with patch('src.connection_manager.ConnectHandler') as mock:
        yield mock

@pytest.fixture
def connection_manager_instance():
    # This ensures a clean instance for each test
    manager = ConnectionManager()
    manager._connections = {}
    yield manager
    manager._connections = {}

def test_creates_separate_connections_for_different_device_types(connection_manager_instance, mock_connect_handler):
    """Verify that the ConnectionManager creates different connections for different device_types with the same IP."""
    router_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios_router",
        username="user",
        password="pass"
    )
    switch_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios_switch",
        username="user",
        password="pass"
    )

    # Mock the ConnectHandler to return a new mock object each time it's called
    mock_connect_handler.side_effect = [MagicMock(), MagicMock()]

    # Get connection for the router
    conn1 = connection_manager_instance.get_connection(router_info, router_info.device_type)

    # Get connection for the switch
    conn2 = connection_manager_instance.get_connection(switch_info, switch_info.device_type)

    assert conn1 is not conn2
    assert mock_connect_handler.call_count == 2

def test_get_connection_passes_timeout(connection_manager_instance, mock_connect_handler):
    """Verify that the ConnectionManager passes the correct timeout to ConnectHandler."""
    from src.config import settings

    device_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios",
        username="user",
        password="pass"
    )

    connection_manager_instance.get_connection(device_info, "cisco_ios")

    mock_connect_handler.assert_called_once_with(
        host=device_info.ip_address,
        username=device_info.username,
        password=device_info.password,
        port=device_info.port,
        device_type="cisco_ios",
        secret=device_info.secret,
        conn_timeout=settings.NETMIKO_TIMEOUT,
    )
