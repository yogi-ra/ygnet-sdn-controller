import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.controllers.features.vlans.cisco_ios import CiscoIosVlans
from src.controllers.features.interfaces.cisco_ios import CiscoIosInterfaces
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


@pytest.fixture
def mock_netmiko_connect_handler(mocker):
    """
    Fixture to mock ConnectionManager.get_connection.
    """
    mock_connection_instance = mocker.Mock()
    mock_connection_instance.send_command.return_value = "" # Default return for send_command
    mock_connection_instance.enable.return_value = None # Mock enable method
    mock_get_connection = mocker.patch(
        "src.connection_manager.ConnectionManager.get_connection",
        return_value=mock_connection_instance
    )
    return mock_get_connection


# --- CiscoIosSwitch Specific Method Tests ---
def test_cisco_switch_get_vlan_brief(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_vlan_brief method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vlan_brief = handler.vlans.get_vlan_brief()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show vlan brief")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan brief", "raw output of show vlan brief", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vlan_brief == expected_data


def test_cisco_switch_get_mac_address_table(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_mac_address_table method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    mac_table = handler.get_mac_address_table()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show mac address-table")
    mock_parse_cli_output.assert_called_once_with(
        "show mac address-table", "raw output of show mac address-table", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert mac_table == expected_data


def test_cisco_switch_get_interfaces_status(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_status = handler.interfaces.get_interfaces_status()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show interfaces status")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces status", "raw output of show interfaces status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_status == expected_data


def test_cisco_switch_get_vlan_details(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_vlan_details method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vlan_details = handler.vlans.get_vlan_details()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show vlan")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan", "raw output of show vlan", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vlan_details == expected_data


def test_cisco_switch_get_vtp_status(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_vtp_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vtp_status = handler.vlans.get_vtp_status()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show vtp status")
    mock_parse_cli_output.assert_called_once_with(
        "show vtp status", "raw output of show vtp status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vtp_status == expected_data


def test_cisco_switch_get_spanning_tree_summary(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_spanning_tree_summary method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    spanning_tree_summary = handler.get_spanning_tree_summary()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show spanning-tree summary")
    mock_parse_cli_output.assert_called_once_with(
        "show spanning-tree summary", "raw output of show spanning-tree summary", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert spanning_tree_summary == expected_data


def test_cisco_switch_get_interfaces_trunk(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_trunk method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_trunk = handler.interfaces.get_interfaces_trunk()

    mock_netmiko_connect_handler.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show interfaces trunk")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces trunk", "raw output of show interfaces trunk", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_trunk == expected_data


def test_cisco_switch_get_mac_address_table(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_mac_address_table method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    mac_table = handler.get_mac_address_table()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show mac address-table")
    mock_parse_cli_output.assert_called_once_with(
        "show mac address-table", "raw output of show mac address-table", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert mac_table == expected_data


def test_cisco_switch_get_interfaces_status(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_status = handler.interfaces.get_interfaces_status()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show interfaces status")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces status", "raw output of show interfaces status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_status == expected_data


def test_cisco_switch_get_vlan_details(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_vlan_details method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vlan_details = handler.vlans.get_vlan_details()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show vlan")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan", "raw output of show vlan", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vlan_details == expected_data


def test_cisco_switch_get_vtp_status(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_vtp_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vtp_status = handler.vlans.get_vtp_status()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show vtp status")
    mock_parse_cli_output.assert_called_once_with(
        "show vtp status", "raw output of show vtp status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vtp_status == expected_data


def test_cisco_switch_get_spanning_tree_summary(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_spanning_tree_summary method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    spanning_tree_summary = handler.get_spanning_tree_summary()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show spanning-tree summary")
    mock_parse_cli_output.assert_called_once_with(
        "show spanning-tree summary", "raw output of show spanning-tree summary", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert spanning_tree_summary == expected_data


def test_cisco_switch_get_interfaces_trunk(mock_connection_manager, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_trunk method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_trunk = handler.interfaces.get_interfaces_trunk()

    mock_connection_manager.get_connection.assert_called_once_with(
        sample_cisco_switch_info, handler.netmiko_device_type
    )
    mock_send_command.assert_called_once_with("show interfaces trunk")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces trunk", "raw output of show interfaces trunk", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_trunk == expected_data


def test_cisco_switch_get_mac_address_table(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_mac_address_table method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    mac_table = handler.get_mac_address_table()

    mock_send_command.assert_called_once_with("show mac address-table")
    mock_parse_cli_output.assert_called_once_with(
        "show mac address-table", "raw output of show mac address-table", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert mac_table == expected_data


def test_cisco_switch_get_interfaces_status(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_status = handler.interfaces.get_interfaces_status()

    mock_send_command.assert_called_once_with("show interfaces status")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces status", "raw output of show interfaces status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_status == expected_data


def test_cisco_switch_get_vlan_details(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_vlan_details method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vlan_details = handler.vlans.get_vlan_details()

    mock_send_command.assert_called_once_with("show vlan")
    mock_parse_cli_output.assert_called_once_with(
        "show vlan", "raw output of show vlan", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vlan_details == expected_data


def test_cisco_switch_get_vtp_status(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_vtp_status method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    vtp_status = handler.vlans.get_vtp_status()

    mock_send_command.assert_called_once_with("show vtp status")
    mock_parse_cli_output.assert_called_once_with(
        "show vtp status", "raw output of show vtp status", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert vtp_status == expected_data


def test_cisco_switch_get_spanning_tree_summary(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_spanning_tree_summary method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    spanning_tree_summary = handler.get_spanning_tree_summary()

    mock_send_command.assert_called_once_with("show spanning-tree summary")
    mock_parse_cli_output.assert_called_once_with(
        "show spanning-tree summary", "raw output of show spanning-tree summary", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert spanning_tree_summary == expected_data


def test_cisco_switch_get_interfaces_trunk(mock_netmiko_connect_handler, mocker, sample_cisco_switch_info):
    """Test the get_interfaces_trunk method for Cisco IOS Switch devices."""
    mock_send_command = mocker.patch("src.controllers.base.BaseDevice.send_command")
    mock_parse_cli_output = mocker.patch("src.controllers.base.parse_cli_output")
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
    handler.connect() # Ensure connection is established
    interfaces_trunk = handler.interfaces.get_interfaces_trunk()

    mock_send_command.assert_called_once_with("show interfaces trunk")
    mock_parse_cli_output.assert_called_once_with(
        "show interfaces trunk", "raw output of show interfaces trunk", handler.device_info.device_type, handler.netmiko_device_type
    )
    assert interfaces_trunk == expected_data

