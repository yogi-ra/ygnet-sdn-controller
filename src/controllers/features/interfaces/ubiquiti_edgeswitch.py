from .base import BaseInterfaces
from typing import List, Dict, Any, Union

class UbiquitiEdgeSwitchInterfaces(BaseInterfaces):
    """Ubiquiti EdgeSwitch implementation of interface features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    def get_interfaces_brief(self) -> List[Dict[str, Any]]:
        try:
            command = "show interfaces status"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interfaces brief: {e}")
            return []

    def get_interface_config(self, interface_name: str) -> Union[List[Dict[str, Any]], str]:
        try:
            command = f"show running-config interface {interface_name}"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interface config for {interface_name}: {e}")
            return ""

    def get_interfaces_status(self) -> List[Dict[str, Any]]:
        try:
            command = "show interfaces status"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interfaces status: {e}")
            return []

    def get_interfaces_trunk(self) -> List[Dict[str, Any]]:
        try:
            command = "show interfaces switchport"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interfaces trunk: {e}")
            return []

    def get_interface_vlan_membership(self) -> List[Dict[str, Any]]:
        try:
            command = "show interfaces switchport"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interface VLAN membership: {e}")
            return []

    def get_trunk_port_config(self, interface_name: str) -> Union[List[Dict[str, Any]], str]:
        try:
            command = f"show interfaces {interface_name} switchport"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting trunk port config for {interface_name}: {e}")
            return ""

    def get_interface_port_security(self, interface_name: str) -> List[Dict[str, Any]]:
        # Ubiquiti EdgeSwitch may not have direct port security command
        # This is a placeholder implementation
        try:
            command = f"show interfaces {interface_name}"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interface port security for {interface_name}: {e}")
            return []
            
    def configure_interface(self, interface_name: str, config_commands: List[str]) -> bool:
        """
        Configure an interface with the provided commands.
        
        Args:
            interface_name: Name of the interface to configure
            config_commands: List of configuration commands to apply
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            # Enter configuration mode
            config_mode_commands = [
                ["configure", "#"],
                [f"interface {interface_name}", "#"],
                *[[cmd, "#"] for cmd in config_commands],
                ["exit", "#"],
                ["exit", "#"]
            ]
            
            self.device_handler.send_multiline_commands(config_mode_commands)
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error configuring interface {interface_name}: {e}")
            return False
            
    def configure_port_security(self, interface_name: str, max_mac_addresses: int = 1, 
                               violation_action: str = "restrict") -> bool:
        """
        Configure port security on an interface.
        
        Args:
            interface_name: Name of the interface to configure
            max_mac_addresses: Maximum number of MAC addresses allowed (default: 1)
            violation_action: Action to take on violation (default: "restrict")
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            commands = [
                ["configure", "#"],
                [f"interface {interface_name}", "#"],
                ["switchport mode access", "#"],
                ["switchport port-security", "#"],
                [f"switchport port-security maximum {max_mac_addresses}", "#"],
                [f"switchport port-security violation {violation_action}", "#"],
                ["switchport port-security mac-address sticky", "#"],
                ["exit", "#"],
                ["exit", "#"]
            ]
            
            self.device_handler.send_multiline_commands(commands)
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error configuring port security on interface {interface_name}: {e}")
            return False