import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from src.connection_manager import ConnectionManager
from src.device_info import DeviceConnectionInfo
from src.config import settings



@pytest.fixture
def connection_manager_instance():
    # This ensures a clean instance for each test
    manager = ConnectionManager()
    manager._connections = {}
    yield manager
    manager._connections = {}

def test_creates_separate_connections_for_different_device_types(mocker, connection_manager_instance):
    """Verify that the ConnectionManager creates different connections for different device_types with the same IP."""
    router_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios_router",
        username="user",
        password="pass"
    )
    juniper_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="juniper_junos",
        username="user",
        password="pass"
    )

    # Mock the ConnectHandler to avoid real connections
    mock_connect_handler = mocker.patch("src.connection_manager.ConnectHandler")
    mock_connection = MagicMock()
    mock_connect_handler.return_value = mock_connection

    # Get connection for the router
    conn1_future = connection_manager_instance.get_connection(router_info, router_info.device_type)
    conn1 = conn1_future.result() # Get the actual connection from the Future

    # Get connection for the Juniper device
    conn2_future = connection_manager_instance.get_connection(juniper_info, juniper_info.device_type)
    conn2 = conn2_future.result() # Get the actual connection from the Future

    assert conn1 is mock_connection
    assert conn2 is mock_connection
    # Verify that ConnectHandler was called twice with different device types
    assert mock_connect_handler.call_count == 2
    call_args_list = mock_connect_handler.call_args_list
    # The first call should be for cisco_ios and the second for juniper_junos
    assert call_args_list[0][1]["device_type"] == "cisco_ios"
    assert call_args_list[1][1]["device_type"] == "juniper_junos"

def test_get_connection_passes_timeout(mocker, connection_manager_instance):
    """Verify that the ConnectionManager passes the correct timeout to ConnectHandler."""
    device_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios",
        username="user",
        password="pass"
    )

    # Mock the ConnectHandler to avoid real connections
    mock_connect_handler = mocker.patch("src.connection_manager.ConnectHandler")
    mock_connection = MagicMock()
    mock_connect_handler.return_value = mock_connection

    connection_manager_instance.get_connection(device_info, device_info.device_type).result() # Call result() on the Future
    
    # Verify that ConnectHandler was called with the correct timeout
    mock_connect_handler.assert_called_once()
    call_kwargs = mock_connect_handler.call_args[1]
    assert "timeout" in call_kwargs
    assert call_kwargs["timeout"] == settings.NETMIKO_TIMEOUT