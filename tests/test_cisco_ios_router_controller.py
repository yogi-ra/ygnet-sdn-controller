import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.controllers.features.system.cisco_ios import CiscoIosSystem
from src.controllers.features.interfaces.cisco_ios import CiscoIosInterfaces
from src.controllers.features.routing.cisco_ios import CiscoIosRouting
from src.controllers.features.aaa.cisco_ios import CiscoIosAaa
from datetime import datetime
from src.controllers import (
    DeviceConnectionInfo,
    get_device_handler,
    CiscoIosDevice,
    CiscoIosRouter,
    BaseDevice,
)
from src.exceptions import (
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceConnectionError,
)
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException





@pytest.fixture
def sample_cisco_router_info():
    """Provides a sample DeviceConnectionInfo object for a Cisco IOS Router device."""
    return DeviceConnectionInfo(
        name="router.example.com",
        ip_address="10.100.100.2",
        device_type="cisco_ios_router",
        username="testuser",
        password="testpass",
        secret="testsecret",
    )


# --- BaseDevice Tests (via factory) ---
def test_check_reachability_success(mock_connection_manager, sample_cisco_router_info):
    """Test successful reachability check."""
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is True
    mock_connection_manager.assert_called_once_with(
        sample_cisco_router_info, handler.netmiko_device_type
    )


def test_check_reachability_raises_authentication_error(mock_connection_manager, sample_cisco_router_info):
    """Test that check_reachability handles authentication errors."""
    mock_connection_manager.side_effect = NetmikoAuthenticationException
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is False


def test_check_reachability_raises_timeout_error(mock_connection_manager, sample_cisco_router_info):
    """Test that check_reachability handles timeout errors."""
    mock_connection_manager.side_effect = NetmikoTimeoutException
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is False


# --- CiscoIosDevice Specific Method Tests (using router info) ---
# These tests are for methods in CiscoIosDevice, but use the router info fixture
def test_cisco_get_version_info(mock_connection_manager, mocker, sample_cisco_router_info):
    """Test the get_version_info method for Cisco IOS devices."""
    # Mock parse_cli_output on the instance of CiscoIosSystem
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
    expected_data = [
        {
            "name": "csr1000v",
            "version": "16.09.03",
            "rommon": "IOS-XE",
            "uptime": "2 weeks, 2 days, 5 hours, 4 minutes",
            "running_image": "packages.conf",
            "hardware": ["CSR1000V"],
            "serial": ["9MVSHL36S0B"],
            "config_register": "0x2102",
        }
    ]
    mock_connection_manager.return_value.send_command.return_value = "raw output of show version"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        version_info = handler.system.get_version_info()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show version")
    mock_parse_cli_output.assert_called_once_with(
        "show version", "raw output of show version", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert version_info == expected_data[0]


def test_cisco_get_interfaces_brief(mock_connection_manager, mocker, sample_cisco_router_info):
    """Test the get_interfaces_brief method."""
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
    expected_data = [
        {
            "intf": "GigabitEthernet1",
            "ipaddr": "10.1.1.1",
            "status": "up",
            "proto": "up",
        },
        {"intf": "Loopback0", "ipaddr": "1.1.1.1", "status": "up", "proto": "up"},
    ]
    mock_connection_manager.return_value.send_command.return_value = "raw output of show ip interface brief"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        interfaces = handler.interfaces.get_interfaces_brief()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show ip interface brief")
    mock_parse_cli_output.assert_called_once_with(
        "show ip interface brief", "raw output of show ip interface brief", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces == expected_data


def test_cisco_get_hostname(mocker, sample_cisco_router_info):
    """
    Test that get_hostname correctly extracts the hostname.
    """
    # This test relies on the mock of get_version_info
    mock_get_version_info = mocker.patch.object(CiscoIosSystem, "get_version_info")
    mock_get_version_info.return_value = {"hostname": "MyRouter"}

    handler = get_device_handler(sample_cisco_router_info)
    hostname = handler.system.get_hostname()

    assert hostname == "MyRouter"
    mock_get_version_info.assert_called_once()


def test_cisco_get_active_users(mock_connection_manager, mocker, sample_cisco_router_info):
    """
    Test the get_active_users method for Cisco IOS devices.
    """
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
    expected_data = [
        {
            "line": "*  2 vty 0",
            "user": "yogi",
            "hosts": "idle",
            "idle": "00:00:00",
            "location": "10.100.100.1",
        }
    ]
    mock_connection_manager.return_value.send_command.return_value = "raw output of show users"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        active_users = handler.system.get_active_users()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show users")
    mock_parse_cli_output.assert_called_once_with(
        "show users", "raw output of show users", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert active_users == expected_data

def test_cisco_get_clock(mock_connection_manager, sample_cisco_router_info):
    """
    Test the get_clock method parses the output into a datetime object.
    """
    real_device_clock_output = "*13:26:03.945 UTC Thu Aug 21 2025"
    mock_connection_manager.return_value.send_command.return_value = real_device_clock_output

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        clock = handler.system.get_clock()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show clock")
    assert isinstance(clock, datetime)
    assert clock.year == 2025
    assert clock.month == 8
    assert clock.day == 21
    assert clock.hour == 13
    assert clock.minute == 26
    assert clock.second == 3


# --- CiscoIosRouter Specific Method Tests ---
def test_cisco_router_get_routing_table(mock_connection_manager, mocker, sample_cisco_router_info):
    """
    Test the get_routing_table method for Cisco IOS Router devices.
    """
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
    expected_data = [
        {"protocol": "C", "network": "10.0.0.0/24", "interface": "GigabitEthernet0/0"},
        {"protocol": "S", "network": "0.0.0.0/0", "nexthop": "192.168.1.1"},
    ]
    mock_connection_manager.return_value.send_command.return_value = "raw output of show ip route"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        routing_table = handler.routing.get_routing_table()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show ip route")
    mock_parse_cli_output.assert_called_once_with(
        "show ip route", "raw output of show ip route", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert routing_table == expected_data


def test_cisco_router_get_bgp_summary(mock_connection_manager, mocker, sample_cisco_router_info):
    """
    Test the get_bgp_summary method for Cisco IOS Router devices.
    """
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
    expected_data = [
        {
            "local_as": "65000",
            "router_id": "1.1.1.1",
            "neighbor": "10.0.0.2",
            "state_pfxrcd": "Idle",
        }
    ]
    mock_connection_manager.return_value.send_command.return_value = "raw output of show ip bgp summary"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        bgp_summary = handler.routing.get_bgp_summary()

    mock_connection_manager.return_value.send_command.assert_called_once_with("show ip bgp summary")
    mock_parse_cli_output.assert_called_once_with(
        "show ip bgp summary", "raw output of show ip bgp summary", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert bgp_summary == expected_data


def test_cisco_get_local_users(mock_connection_manager, sample_cisco_router_info):
    """Test the get_local_users method for Cisco IOS devices."""
    raw_output = (
        "username admin privilege 15 secret 5 $1$abc$xyz\n"
        "username guest password 0 guestpass\n"
        "username network_ops privilege 1 secret 5 $1$def$uvw"
    )
    mock_connection_manager.return_value.send_command.return_value = raw_output

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        local_users = handler.system.get_local_users()

    expected_users = [
        {"username": "admin", "privilege": "15"},
        {"username": "guest"},
        {"username": "network_ops", "privilege": "1"},
    ]

    assert local_users == expected_users
    mock_connection_manager.return_value.send_command.assert_called_once_with(
        "show running-config | include ^username"
    )


