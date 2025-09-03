import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime
from src.controllers import (
    DeviceConnectionInfo,
    get_device_handler,
)
from tests.conftest import create_future_with_result
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


@pytest.fixture
def sample_cisco_router_info():
    """
    Provides a sample DeviceConnectionInfo object for a Cisco IOS Router device.
    """
    return DeviceConnectionInfo(
        name="router.example.com",
        ip_address="10.100.100.2",
        device_type="cisco_ios_router",
        username="testuser",
        password="testpass",
        secret="testsecret",
    )


# --- BaseDevice Tests (via factory) ---
def test_check_reachability_success(sample_cisco_router_info, mock_connection_manager_instance):
    """Test successful reachability check."""
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is True
    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_router_info, handler.netmiko_device_type
    )


def test_check_reachability_raises_authentication_error(sample_cisco_router_info, mock_connection_manager_instance):
    """Test that check_reachability handles authentication errors."""
    mock_connection_manager_instance["get_connection"].side_effect = NetmikoAuthenticationException
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is False
    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_router_info, handler.netmiko_device_type
    )


def test_check_reachability_raises_timeout_error(sample_cisco_router_info, mock_connection_manager_instance):
    """Test that check_reachability handles timeout errors."""
    mock_connection_manager_instance["get_connection"].side_effect = NetmikoTimeoutException
    handler = get_device_handler(sample_cisco_router_info)
    assert handler.check_reachability() is False
    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_router_info, handler.netmiko_device_type
    )


# --- CiscoIosDevice Specific Method Tests (using router info) ---
# These tests are for methods in CiscoIosDevice, but use the router info fixture
def test_cisco_get_version_info(mocker, sample_cisco_router_info, mock_connection_manager_instance):
    """Test the get_version_info method for Cisco IOS devices."""
    raw_version_output = "raw output of show version"
    expected_data = [
        {
            "software_image": "Cisco IOS Software",
            "version": "15.4(3)M5",
            "hostname": "Router1",
        }
    ]
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_version_output)

    handler = get_device_handler(sample_cisco_router_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        version_info = handler.system.get_version_info()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show version", handler.netmiko_device_type)
    handler.parse_cli_output.assert_called_once_with("show version", raw_version_output)
    assert version_info == expected_data


def test_cisco_get_interfaces_brief(mocker, sample_cisco_router_info, mock_connection_manager_instance):
    """Test the get_interfaces_brief method."""
    raw_interfaces_brief_output = "raw output of show ip interface brief"
    expected_data = [
        {"interface": "GigabitEthernet0/0", "ip_address": "192.168.1.1", "status": "up", "proto": "up"},
        {"interface": "Loopback0", "ip_address": "10.0.0.1", "status": "up", "proto": "up"},
    ]
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_interfaces_brief_output)

    handler = get_device_handler(sample_cisco_router_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        interfaces = handler.interfaces.get_interfaces_brief()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show ip interface brief", handler.netmiko_device_type)
    handler.parse_cli_output.assert_called_once_with("show ip interface brief", raw_interfaces_brief_output)
    assert interfaces == expected_data


def test_cisco_get_hostname(mocker, sample_cisco_router_info):
    """
    Test that get_hostname correctly extracts the hostname.
    """
    # This test relies on the mock of get_version_info
    mock_get_version_info = mocker.patch.object(handler.system, "get_version_info")
    mock_get_version_info.return_value = [{"hostname": "MyRouter"}]

    handler = get_device_handler(sample_cisco_router_info)
    hostname = handler.system.get_hostname()

    assert hostname == "MyRouter"
    mock_get_version_info.assert_called_once()


def test_cisco_get_active_users(mocker, sample_cisco_router_info, mock_connection_manager_instance):
    """
    Test the get_active_users method for Cisco IOS devices.
    """
    raw_active_users_output = "raw output of show users"
    expected_data = [
        {"user": "admin", "line": "vty0", "idle": "00:00:00", "location": "192.168.1.100"},
        {"user": "guest", "line": "vty1", "idle": "00:01:00", "location": "192.168.1.101"},
    ]
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_active_users_output)

    handler = get_device_handler(sample_cisco_router_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        active_users = handler.system.get_active_users()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show users", handler.netmiko_device_type)
    handler.parse_cli_output.assert_called_once_with("show users", raw_active_users_output)
    assert active_users == expected_data

def test_cisco_get_clock(sample_cisco_router_info, mocker, mock_connection_manager_instance):
    """
    Test the get_clock method.
    """
    real_device_clock_output = "*13:26:03.945 UTC Thu Aug 21 2025"
    expected_data = "13:26:03.945 UTC Thu Aug 21 2025"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(real_device_clock_output)

    handler = get_device_handler(sample_cisco_router_info)

    with handler:
        clock = handler.system.get_clock()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show clock", handler.netmiko_device_type)
    # get_clock doesn't use parse_cli_output, so we don't assert its call
    assert clock == expected_data


# --- CiscoIosRouter Specific Method Tests ---
def test_cisco_router_get_routing_table(mocker, sample_cisco_router_info, mock_connection_manager_instance):
    """
    Test the get_routing_table method for Cisco IOS Router devices.
    """
    raw_routing_table_output = "raw output of show ip route"
    expected_data = [
        {"protocol": "C", "network": "192.168.1.0/24", "nexthop_ip": "0.0.0.0", "nexthop_if": "GigabitEthernet0/0"},
        {"protocol": "S", "network": "0.0.0.0/0", "nexthop_ip": "10.0.0.1", "nexthop_if": "GigabitEthernet0/1"},
    ]
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_routing_table_output)

    handler = get_device_handler(sample_cisco_router_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        routing_table = handler.routing.get_routing_table()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show ip route", handler.netmiko_device_type)
    handler.parse_cli_output.assert_called_once_with("show ip route", raw_routing_table_output)
    assert routing_table == expected_data


def test_cisco_router_get_bgp_summary(mocker, sample_cisco_router_info, mock_connection_manager_instance):
    """
    Test the get_bgp_summary method for Cisco IOS Router devices.
    """
    raw_bgp_summary_output = "raw output of show ip bgp summary"
    expected_data = [
        {"neighbor": "10.0.0.2", "remote_as": "65002", "state_pfxrcd": "Idle"},
    ]
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_bgp_summary_output)

    handler = get_device_handler(sample_cisco_router_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        bgp_summary = handler.routing.get_bgp_summary()

    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show ip bgp summary", handler.netmiko_device_type)
    handler.parse_cli_output.assert_called_once_with("show ip bgp summary", raw_bgp_summary_output)
    assert bgp_summary == expected_data


def test_cisco_get_local_users(sample_cisco_router_info, mocker, mock_connection_manager_instance):
    """
    Test the get_local_users method for Cisco IOS devices.
    """
    # mock_parse_cli_output = mocker.patch("src.parsing_utils.parse_cli_output")
    raw_output = (
        "username admin privilege 15 secret 5 $1$abc$xyz\n"
        "username guest password 0 guestpass\n"
        "username network_ops privilege 1 secret 5 $1$def$uvw"
    )
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_output)

    handler = get_device_handler(sample_cisco_router_info)
    with handler:
        local_users = handler.system.get_local_users()

    expected_users = [
        {"username": "admin", "privilege": "15"},
        {"username": "guest"},
        {"username": "network_ops", "privilege": "1"},
    ]

    assert local_users == expected_users
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_router_info, "show running-config | include ^username", handler.netmiko_device_type)
    # The parse_cli_output is not used in get_local_users, so we don't assert its call
    # mock_parse_cli_output.assert_called_once_with(
    #     "show running-config | include ^username", raw_output, handler.device_info.device_type, handler.netmiko_device_type
    # )


def test_cisco_router_get_supported_features(sample_cisco_router_info):
    """
    Test that Cisco IOS Router returns the correct supported features.
    """
    handler = get_device_handler(sample_cisco_router_info)
    view_features, action_features = handler.get_supported_features()
    
    # Check that we get the expected features
    expected_view_features = [
        "system_version",
        "system_hostname",
        "system_uptime",
        "system_clock",
        "interfaces_brief",
        "interfaces_status"
    ]
    
    expected_action_features = [
        "interface_state_toggle",
        "system_reboot"
    ]
    
    assert view_features == expected_view_features
    assert action_features == expected_action_features