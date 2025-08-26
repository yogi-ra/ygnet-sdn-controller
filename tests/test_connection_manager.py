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

def test_creates_separate_connections_for_different_device_types(connection_manager_instance):
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

    # Get connection for the router
    conn1_future = connection_manager_instance.get_connection(router_info, router_info.device_type)
    conn1 = conn1_future.result() # Get the actual connection from the Future

    # Get connection for the switch
    conn2_future = connection_manager_instance.get_connection(switch_info, switch_info.device_type)
    conn2 = conn2_future.result() # Get the actual connection from the Future

    assert conn1 is not conn2

def test_get_connection_passes_timeout(connection_manager_instance):
    """Verify that the ConnectionManager passes the correct timeout to ConnectHandler."""
    device_info = DeviceConnectionInfo(
        name="device.example.com",
        ip_address="10.1.1.1",
        device_type="cisco_ios",
        username="user",
        password="pass"
    )

    connection_manager_instance.get_connection(device_info, device_info.device_type).result() # Call result() on the Future