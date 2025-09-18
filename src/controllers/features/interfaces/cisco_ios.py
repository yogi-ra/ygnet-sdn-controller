from ..interfaces.base import BaseInterfaces
from typing import List, Dict, Any, Union
import threading

class CiscoIosInterfaces(BaseInterfaces):
    """Cisco IOS implementation of interface features."""

    def get_interfaces_brief(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip interface brief"
            raw_output = self.device_handler.send_command(command)
            parsed_output = self.device_handler.parse_cli_output(command, raw_output)
            
            # Add 'enabled' field based on 'Status' - True if administratively up, False if administratively down
            # Also add status information for frontend display
            for interface in parsed_output:
                status = interface.get("status", "").lower()
                # Set to False only if explicitly administratively down
                if "administratively down" in status:
                    interface["enabled"] = False
                else:
                    # For all other states (up, down, etc.), consider it enabled from admin perspective
                    interface["enabled"] = True
                
                # Add descriptive status for display
                if "administratively down" in status:
                    interface["status_description"] = "Administratively Down"
                elif "up" in status and "down" in status:
                    interface["status_description"] = "Operationally Down (Admin Up)"
                elif "up" in status:
                    interface["status_description"] = "Up"
                else:
                    interface["status_description"] = status.title()
            
            return parsed_output
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
            command = "show interfaces trunk"
            raw_output = self.device_handler.send_command(command)
            parsed_output = self.device_handler.parse_cli_output(command, raw_output)
            return parsed_output if parsed_output else self._parse_interfaces_trunk(raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interfaces trunk: {e}")
            return []

    def _parse_interfaces_trunk(self, raw_output: str) -> List[Dict[str, Any]]:
        trunk_data = []
        for line in raw_output.splitlines():
            if "trunking" in line and "802.1q" in line:
                parts = line.split()
                if len(parts) >= 5:
                    trunk_data.append({
                        "port": parts[0],
                        "mode": parts[1],
                        "encapsulation": parts[2],
                        "status": parts[3],
                        "native_vlan": parts[4],
                    })
        return trunk_data

    def get_interface_vlan_membership(self) -> List[Dict[str, Any]]:
        try:
            command = "show interface switchport"
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
        try:
            command = f"show port-security interface {interface_name}"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting interface port security for {interface_name}: {e}")
            return []

    def set_interface_state(self, interface_name: str, enabled: bool) -> str:
        """
        Enables or disables a specific interface.
        """
        state = "no shutdown" if enabled else "shutdown"
        commands = [
            f"interface {interface_name}",
            state
        ]
        try:
            output = self.device_handler.send_config_set(commands)
            return output
        except Exception as e:
            self.device_handler.logger.error(f"Error setting interface state for {interface_name}: {e}")
            return str(e)

    def configure_interface(self, interface_name: str, config_commands: List[str]) -> str:
        """
        Configures an interface with the provided commands.
        
        Args:
            interface_name: Name of the interface to configure
            config_commands: List of configuration commands to apply
            
        Returns:
            Output from the configuration commands
        """
        commands = [
            f"interface {interface_name}",
            *config_commands,
            "exit"
        ]
        try:
            output = self.device_handler.send_config_set(commands)
            return output
        except Exception as e:
            self.device_handler.logger.error(f"Error configuring interface {interface_name}: {e}")
            return str(e)

    def configure_interface_vlan(self, interface_config: Dict[str, Any]) -> bool:
        """
        Configure VLAN settings for an interface (access or trunk mode).
        
        Args:
            interface_config: Dictionary containing interface VLAN configuration parameters
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            commands = [
                f"interface {interface_config['interface_name']}",
            ]

            if interface_config['mode'] == "access":
                commands.append("switchport mode access")
                if interface_config.get('access_vlan'):
                    commands.append(f"switchport access vlan {interface_config['access_vlan']}")
            elif interface_config['mode'] == "trunk":
                commands.append("switchport mode trunk")
                if interface_config.get('allowed_vlans'):
                    commands.append(f"switchport trunk allowed vlan {interface_config['allowed_vlans']}")
                if interface_config.get('native_vlan'):
                    commands.append(f"switchport trunk native vlan {interface_config['native_vlan']}")
            
            self.device_handler.send_config_set(commands)
            # Clear cache asynchronously to avoid blocking the response
            threading.Thread(target=self._clear_interface_vlan_cache_async).start()
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error configuring interface VLAN for {interface_config.get('interface_name')}: {e}")
            return False

    def _clear_interface_vlan_cache_async(self):
        """Asynchronously clear interface and VLAN-related cache entries."""
        try:
            self.device_handler.clear_cache(["device_vlans_brief", "device_interfaces_brief"])
        except Exception as e:
            self.device_handler.logger.error(f"Error clearing interface/VLAN cache: {e}")