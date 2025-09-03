import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.controllers import (
    DeviceConnectionInfo,
    get_device_handler,
)
from tests.conftest import create_future_with_result


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
def test_cisco_switch_get_vlan_brief(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_vlan_brief method for Cisco IOS Switch devices."""
    expected_data = [
        {
            "vlan_id": "1",
            "name": "default",
            "status": "active",
            "ports": "Fa0/1, Fa0/2",
        },
        {"vlan_id": "10", "name": "VLAN10", "status": "active", "ports": "Fa0/3"},
    ]
    # mock_connection_manager.return_value.send_command.return_value = "raw output of show vlan brief" # Removed
    raw_vlan_brief_output = "raw output of show vlan brief"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_vlan_brief_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        vlan_brief = handler.vlans.get_vlan_brief()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    # mock_connection_manager.return_value.send_command.assert_called_once_with("show vlan brief") # Removed
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show vlan brief", handler.netmiko_device_type) # Added
    handler.parse_cli_output.assert_called_once_with("show vlan brief", raw_vlan_brief_output)
    assert vlan_brief == expected_data


def test_cisco_switch_get_vlan_details(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_vlan_details method for Cisco IOS Switch devices."""
    expected_data = [
        {
            "vlan_id": "1",
            "name": "default",
            "status": "active",
            "ports": "Fa0/1, Fa0/2",
        },
        {"vlan_id": "10", "name": "VLAN10", "status": "active", "ports": "Fa0/3"},
    ]
    # mock_connection_manager.return_value.send_command.return_value = "raw output of show vlan" # Removed
    raw_vlan_details_output = "raw output of show vlan"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_vlan_details_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        vlan_details = handler.vlans.get_vlan_details()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    # mock_connection_manager.return_value.send_command.assert_called_once_with("show vlan") # Removed
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show vlan", handler.netmiko_device_type) # Added
    handler.parse_cli_output.assert_called_once_with("show vlan", raw_vlan_details_output)
    assert vlan_details == expected_data


def test_cisco_switch_get_vtp_status(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_vtp_status method for Cisco IOS Switch devices."""

    expected_data = [
        {
            "vtp_version": "2",
            "configuration_revision": "5",
            "max_vlans": "256",
            "mode": "server",
            "domain_name": "VTP_DOMAIN",
        }
    ]
    # mock_send_command.return_value = "raw output of show vtp status" # Removed
    raw_vtp_status_output = "raw output of show vtp status"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_vtp_status_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        vtp_status = handler.vlans.get_vtp_status()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show vtp status", handler.netmiko_device_type) # Changed from mock_send_command
    handler.parse_cli_output.assert_called_once_with("show vtp status", raw_vtp_status_output)
    assert vtp_status == expected_data


def test_cisco_switch_get_spanning_tree_summary(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_spanning_tree_summary method for Cisco IOS Switch devices."""

    expected_data = [
        {
            "vlan": "1",
            "root_id": "0000.0000.0000",
            "root_port": "Fa0/1",
            "cost": "19",
            "status": "forwarding",
        }
    ]
    # mock_send_command.return_value = "raw output of show spanning-tree summary" # Removed
    raw_spanning_tree_summary_output = "raw output of show spanning-tree summary"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_spanning_tree_summary_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        spanning_tree_summary = handler.vlans.get_spanning_tree_summary()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show spanning-tree summary", handler.netmiko_device_type) # Changed from mock_send_command
    handler.parse_cli_output.assert_called_once_with("show spanning-tree summary", raw_spanning_tree_summary_output)
    assert spanning_tree_summary == expected_data


def test_cisco_switch_get_interfaces_trunk(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_interfaces_trunk method for Cisco IOS Switch devices."""

    expected_data = [
        {
            "port": "Fa0/1",
            "mode": "on",
            "encapsulation": "dot1q",
            "status": "trunking",
            "vlans_allowed": "1-4094",
        }
    ]
    # mock_send_command.return_value = "raw output of show interfaces trunk" # Removed
    raw_interfaces_trunk_output = "raw output of show interfaces trunk"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_interfaces_trunk_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        interfaces_trunk = handler.interfaces.get_interfaces_trunk()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show interfaces trunk", handler.netmiko_device_type) # Changed from mock_send_command
    handler.parse_cli_output.assert_called_once_with("show interfaces trunk", raw_interfaces_trunk_output)
    assert interfaces_trunk == expected_data


def test_cisco_switch_get_interfaces_status(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_interfaces_status method for Cisco IOS Switch devices."""

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
    # mock_send_command.return_value = "raw output of show interfaces status" # Removed
    raw_interfaces_status_output = "raw output of show interfaces status"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_interfaces_status_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        interfaces_status = handler.interfaces.get_interfaces_status()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show interfaces status", handler.netmiko_device_type) # Changed from mock_send_command
    handler.parse_cli_output.assert_called_once_with("show interfaces status", raw_interfaces_status_output)
    assert interfaces_status == expected_data


def test_cisco_switch_get_mac_address_table(
    mocker, sample_cisco_switch_info, mock_connection_manager_instance
):
    """Test the get_mac_address_table method for Cisco IOS Switch devices."""

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
    # mock_send_command.return_value = "raw output of show mac address-table" # Removed
    raw_mac_address_table_output = "raw output of show mac address-table"
    mock_connection_manager_instance["send_command"].side_effect = lambda device_info, command, netmiko_device_type=None, **kwargs: create_future_with_result(raw_mac_address_table_output)

    handler = get_device_handler(sample_cisco_switch_info)
    # Mock the parse_cli_output method on the specific handler instance
    handler.parse_cli_output = mocker.MagicMock(return_value=expected_data)

    with handler:
        mac_table = handler.vlans.get_mac_address_table()

    mock_connection_manager_instance["get_connection"].assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_connection_manager_instance["send_command"].assert_called_once_with(sample_cisco_switch_info, "show mac address-table", handler.netmiko_device_type) # Changed from mock_send_command
    handler.parse_cli_output.assert_called_once_with("show mac address-table", raw_mac_address_table_output)
    assert mac_table == expected_data


def test_cisco_switch_get_supported_features(sample_cisco_switch_info):
    """
    Test that Cisco IOS Switch returns the correct supported features.
    """
    handler = get_device_handler(sample_cisco_switch_info)
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