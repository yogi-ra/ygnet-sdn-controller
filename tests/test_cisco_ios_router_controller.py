import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
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
# These tests are general and can be kept in a base test file or duplicated if needed.
# For now, I'll include them here as they use sample_cisco_router_info
def test_connect_success(mocker, sample_cisco_router_info):
    """Test successful connection using the IP address."""
    mock_connect_handler = mocker.patch("src.controllers.base.ConnectHandler")

    handler = get_device_handler(sample_cisco_router_info)
    handler.connect()

    mock_connect_handler.assert_called_once_with(
        host=sample_cisco_router_info.ip_address,  # Verify connection is via IP
        username=sample_cisco_router_info.username,
        password=sample_cisco_router_info.password,
        port=sample_cisco_router_info.port,  # Include port in the assertion
        device_type=handler.netmiko_device_type,  # Use netmiko_device_type
        secret=sample_cisco_router_info.secret,
    )
    handler.connection.enable.assert_called_once()


def test_connect_raises_authentication_error(mocker, sample_cisco_router_info):
    """Test that DeviceAuthenticationError is raised correctly."""
    mocker.patch(
        "src.controllers.base.ConnectHandler",
        side_effect=NetmikoAuthenticationException,
    )
    handler = get_device_handler(sample_cisco_router_info)
    with pytest.raises(DeviceAuthenticationError):
        handler.connect()


def test_connect_raises_timeout_error(mocker, sample_cisco_router_info):
    """Test that DeviceTimeoutError is raised correctly."""
    mocker.patch(
        "src.controllers.base.ConnectHandler", side_effect=NetmikoTimeoutException
    )
    handler = get_device_handler(sample_cisco_router_info)
    with pytest.raises(DeviceTimeoutError):
        handler.connect()


# --- CiscoIosDevice Specific Method Tests (using router info) ---
# These tests are for methods in CiscoIosDevice, but use the router info fixture
def test_cisco_get_version_info(mocker, sample_cisco_router_info):
    """Test the get_version_info method for Cisco IOS devices."""
    mock_send_command = mocker.patch.object(CiscoIosDevice, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosDevice, "parse_cli_output")
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
    mock_send_command.return_value = "raw output of show version"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    version_info = handler.get_version_info()

    mock_send_command.assert_called_once_with("show version")
    mock_parse_cli_output.assert_called_once_with(
        "show version", "raw output of show version"
    )
    assert version_info == expected_data[0]


def test_cisco_get_interfaces_brief(mocker, sample_cisco_router_info):
    """Test the get_interfaces_brief method."""
    mock_send_command = mocker.patch.object(CiscoIosDevice, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosDevice, "parse_cli_output")
    expected_data = [
        {
            "intf": "GigabitEthernet1",
            "ipaddr": "10.1.1.1",
            "status": "up",
            "proto": "up",
        },
        {"intf": "Loopback0", "ipaddr": "1.1.1.1", "status": "up", "proto": "up"},
    ]
    mock_send_command.return_value = "raw output of show ip interface brief"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    interfaces = handler.get_interfaces_brief()

    mock_send_command.assert_called_once_with("show ip interface brief")
    mock_parse_cli_output.assert_called_once_with(
        "show ip interface brief", "raw output of show ip interface brief"
    )
    assert interfaces == expected_data


def test_cisco_get_hostname(mocker, sample_cisco_router_info):
    """
    Test that get_hostname correctly extracts the hostname.
    """
    # This test relies on the mock of get_version_info
    mock_handler = mocker.patch.object(CiscoIosDevice, "get_version_info")
    mock_handler.return_value = {"hostname": "MyRouter"}

    handler = get_device_handler(sample_cisco_router_info)
    hostname = handler.get_hostname()

    assert hostname == "MyRouter"
    mock_handler.assert_called_once()


def test_cisco_get_active_users(mocker, sample_cisco_router_info):
    """
    Test the get_active_users method for Cisco IOS devices.
    """
    mock_send_command = mocker.patch.object(CiscoIosDevice, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosDevice, "parse_cli_output")
    expected_data = [
        {
            "line": "*  2 vty 0",
            "user": "yogi",
            "hosts": "idle",
            "idle": "00:00:00",
            "location": "10.100.100.1",
        }
    ]
    mock_send_command.return_value = "raw output of show users"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    active_users = handler.get_active_users()

    mock_send_command.assert_called_once_with("show users")
    mock_parse_cli_output.assert_called_once_with(
        "show users", "raw output of show users"
    )
    assert active_users == expected_data


def test_cisco_get_clock(mocker, sample_cisco_router_info):
    """
    Test the get_clock method parses the output into a datetime object.
    """
    mock_handler = mocker.patch.object(CiscoIosDevice, "send_command")
    # Example output from a real device
    real_device_clock_output = "*13:26:03.945 UTC Thu Aug 21 2025"
    mock_handler.return_value = real_device_clock_output

    handler = get_device_handler(sample_cisco_router_info)
    clock = handler.get_clock()

    mock_handler.assert_called_once_with(command="show clock")
    assert isinstance(clock, datetime)
    assert clock.year == 2025
    assert clock.month == 8
    assert clock.day == 21
    assert clock.hour == 13
    assert clock.minute == 26
    assert clock.second == 3


# --- CiscoIosRouter Specific Method Tests ---
def test_cisco_router_get_routing_table(mocker, sample_cisco_router_info):
    """
    Test the get_routing_table method for Cisco IOS Router devices.
    """
    mock_send_command = mocker.patch.object(CiscoIosRouter, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosRouter, "parse_cli_output")
    expected_data = [
        {"protocol": "C", "network": "10.0.0.0/24", "interface": "GigabitEthernet0/0"},
        {"protocol": "S", "network": "0.0.0.0/0", "nexthop": "192.168.1.1"},
    ]
    mock_send_command.return_value = "raw output of show ip route"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    routing_table = handler.get_routing_table()

    mock_send_command.assert_called_once_with("show ip route")
    mock_parse_cli_output.assert_called_once_with(
        "show ip route", "raw output of show ip route"
    )
    assert routing_table == expected_data


def test_cisco_router_get_bgp_summary(mocker, sample_cisco_router_info):
    """
    Test the get_bgp_summary method for Cisco IOS Router devices.
    """
    mock_send_command = mocker.patch.object(CiscoIosRouter, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosRouter, "parse_cli_output")
    expected_data = [
        {
            "local_as": "65000",
            "router_id": "1.1.1.1",
            "neighbor": "10.0.0.2",
            "state_pfxrcd": "Idle",
        }
    ]
    mock_send_command.return_value = "raw output of show ip bgp summary"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_router_info)
    bgp_summary = handler.get_bgp_summary()

    mock_send_command.assert_called_once_with("show ip bgp summary")
    mock_parse_cli_output.assert_called_once_with(
        "show ip bgp summary", "raw output of show ip bgp summary"
    )
    assert bgp_summary == expected_data


def test_cisco_get_local_users_with_parsing_utils(mocker, sample_cisco_router_info):
    """
    Test the get_local_users method after refactoring to use parsing_utils.
    """
    mock_send_command = mocker.patch.object(CiscoIosDevice, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosDevice, "parse_cli_output")

    # Mock the raw output that send_command would return
    raw_output = (
        "username admin privilege 15 secret 5 $1$abc$xyz\n"
        "username guest password 0 guestpass\n"
        "username network_ops privilege 1 secret 5 $1$def$uvw"
    )
    mock_send_command.return_value = raw_output

    # Mock the parsed output that parse_cli_output would return
    expected_parsed_data = [
        {"username": "admin", "privilege": "15"},
        {"username": "guest"},
        {"username": "network_ops", "privilege": "1"},
    ]
    mock_parse_cli_output.return_value = expected_parsed_data

    handler = get_device_handler(sample_cisco_router_info)
    local_users = handler.get_local_users()

    mock_send_command.assert_called_once_with(
        command="show running-config | include ^username"
    )
    mock_parse_cli_output.assert_called_once_with(
        "show running-config | include ^username", raw_output
    )
    assert local_users == expected_parsed_data
