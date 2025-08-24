import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime
from src.controllers import (
    DeviceConnectionInfo,
    get_device_handler,
    CiscoIosDevice,
    CiscoIosSwitch,
    BaseDevice,
)
from src.exceptions import (
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceConnectionError,
)
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


@pytest.fixture
def sample_cisco_switch_info():
    """Provides a sample DeviceConnectionInfo object for a Cisco IOS Switch device."""
    return DeviceConnectionInfo(
        name="switch.example.com",
        ip_address="10.100.100.3",
        device_type="cisco_ios_switch",
        username="testuser",
        password="testpass",
        secret="testsecret",
    )


# --- CiscoIosSwitch Specific Method Tests ---
def test_cisco_switch_get_vlan_brief(mocker, sample_cisco_switch_info):
    """Test the get_vlan_brief method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "vlan_id": "1",
            "name": "default",
            "status": "active",
            "ports": "Fa0/1, Fa0/2",
        },
        {"vlan_id": "10", "name": "VLAN10", "status": "active", "ports": "Fa0/3"},
    ]
    mock_send_command.return_value = "raw output of show vlan brief"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    vlan_brief = handler.get_vlan_brief()

    mock_send_command.assert_called_once_with("show vlan brief")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan brief", "raw output of show vlan brief"
    )
    assert vlan_brief == expected_data


def test_cisco_switch_get_mac_address_table(mocker, sample_cisco_switch_info):
    """Test the get_mac_address_table method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "vlan": "1",
            "mac_address": "0000.0000.0001",
            "type": "DYNAMIC",
            "ports": "Fa0/1",
        },
        {
            "vlan": "10",
            "mac_address": "0000.0000.0002",
            "type": "STATIC",
            "ports": "Fa0/2",
        },
    ]
    mock_send_command.return_value = "raw output of show mac address-table"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    mac_table = handler.get_mac_address_table()

    mock_send_command.assert_called_once_with("show mac address-table")
    mock_parse_cli_output.assert_called_once_with(
        "show mac address-table", "raw output of show mac address-table"
    )
    assert mac_table == expected_data


def test_cisco_switch_get_interfaces_status(mocker, sample_cisco_switch_info):
    """Test the get_interfaces_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "port": "Fa0/1",
            "name": "VLAN1",
            "status": "connected",
            "vlan": "1",
            "duplex": "full",
            "speed": "100",
            "type": "10/100BaseTX",
        },
        {
            "port": "Fa0/2",
            "name": "VLAN1",
            "status": "notconnect",
            "vlan": "1",
            "duplex": "auto",
            "speed": "auto",
            "type": "10/100BaseTX",
        },
    ]
    mock_send_command.return_value = "raw output of show interfaces status"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    interfaces_status = handler.get_interfaces_status()

    mock_send_command.assert_called_once_with("show interfaces status")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces status", "raw output of show interfaces status"
    )
    assert interfaces_status == expected_data


def test_cisco_switch_get_vlan_details(mocker, sample_cisco_switch_info):
    """Test the get_vlan_details method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "vlan_id": "1",
            "name": "default",
            "status": "active",
            "ports": "Fa0/1, Fa0/2",
        },
        {"vlan_id": "10", "name": "VLAN10", "status": "active", "ports": "Fa0/3"},
    ]
    mock_send_command.return_value = "raw output of show vlan"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    vlan_details = handler.get_vlan_details()

    mock_send_command.assert_called_once_with("show vlan")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan", "raw output of show vlan"
    )
    assert vlan_details == expected_data


def test_cisco_switch_get_vtp_status(mocker, sample_cisco_switch_info):
    """Test the get_vtp_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "vtp_version": "2",
            "configuration_revision": "5",
            "max_vlans": "256",
            "mode": "server",
            "domain_name": "VTP_DOMAIN",
        }
    ]
    mock_send_command.return_value = "raw output of show vtp status"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    vtp_status = handler.get_vtp_status()

    mock_send_command.assert_called_once_with("show vtp status")
    mock_parse_cli_output.assert_called_once_with(
        "show vtp status", "raw output of show vtp status"
    )
    assert vtp_status == expected_data


def test_cisco_switch_get_spanning_tree_summary(mocker, sample_cisco_switch_info):
    """Test the get_spanning_tree_summary method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "vlan": "1",
            "root_id": "0000.0000.0000",
            "root_port": "Fa0/1",
            "cost": "19",
            "status": "forwarding",
        }
    ]
    mock_send_command.return_value = "raw output of show spanning-tree summary"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    spanning_tree_summary = handler.get_spanning_tree_summary()

    mock_send_command.assert_called_once_with("show spanning-tree summary")
    mock_parse_cli_output.assert_called_once_with(
        "show spanning-tree summary", "raw output of show spanning-tree summary"
    )
    assert spanning_tree_summary == expected_data


def test_cisco_switch_get_interfaces_trunk(mocker, sample_cisco_switch_info):
    """Test the get_interfaces_trunk method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch.object(CiscoIosSwitch, "send_command")
    mock_parse_cli_output = mocker.patch.object(CiscoIosSwitch, "parse_cli_output")
    expected_data = [
        {
            "port": "Fa0/1",
            "mode": "on",
            "encapsulation": "dot1q",
            "status": "trunking",
            "vlans_allowed": "1-4094",
        }
    ]
    mock_send_command.return_value = "raw output of show interfaces trunk"
    mock_parse_cli_output.return_value = expected_data

    handler = get_device_handler(sample_cisco_switch_info)
    interfaces_trunk = handler.get_interfaces_trunk()

    mock_send_command.assert_called_once_with("show interfaces trunk")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces trunk", "raw output of show interfaces trunk"
    )
    assert interfaces_trunk == expected_data

