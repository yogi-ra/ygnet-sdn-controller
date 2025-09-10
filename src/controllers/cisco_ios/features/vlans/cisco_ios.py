from ....features.vlans.base import BaseVlans
from typing import List, Dict, Any
import threading

class CiscoIosVlans(BaseVlans):
    """Cisco IOS implementation of VLAN features."""

    def get_vlan_brief(self) -> List[Dict[str, Any]]:
        try:
            command = "show vlan brief"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VLAN brief: {e}")
            return []

    def get_vlan_details(self) -> List[Dict[str, Any]]:
        try:
            command = "show vlan"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VLAN details: {e}")
            return []

    def get_vtp_status(self) -> List[Dict[str, Any]]:
        try:
            command = "show vtp status"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VTP status: {e}")
            return []

    def get_vlan_config(self) -> List[Dict[str, Any]]:
        try:
            command = "show running-config | section vlan"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VLAN config: {e}")
            return []

    def get_mac_address_table(self) -> List[Dict[str, Any]]:
        try:
            command = "show mac address-table"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting MAC address table: {e}")
            return []

    def get_spanning_tree_summary(self) -> List[Dict[str, Any]]:
        try:
            command = "show spanning-tree summary"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting spanning-tree summary: {e}")
            return []

    def assign_port_to_vlan(self, vlan_id: int, port: str) -> bool:
        try:
            commands = [
                f"interface {port}",
                f"switchport access vlan {vlan_id}",
            ]
            self.device_handler.send_config_set(commands)
            # Clear cache asynchronously to avoid blocking the response
            threading.Thread(target=self._clear_vlan_cache_async).start()
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error assigning port {port} to VLAN {vlan_id}: {e}")
            return False

    def _clear_vlan_cache_async(self):
        """Asynchronously clear VLAN-related cache entries."""
        try:
            self.device_handler.clear_cache(["device_vlans_brief"])
        except Exception as e:
            self.device_handler.logger.error(f"Error clearing VLAN cache: {e}")

    def configure_interface_vlan(self, interface_config: dict) -> bool:
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

    def create_vlan(self, vlan_id: int, name: str = None) -> bool:
        """Create a new VLAN."""
        try:
            commands = [f"vlan {vlan_id}"]
            if name:
                commands.append(f"name {name}")
            self.device_handler.send_config_set(commands)
            # Clear VLAN cache asynchronously
            threading.Thread(target=self._clear_vlan_cache_async).start()
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error creating VLAN {vlan_id}: {e}")
            return False

    def change_vlan_name(self, vlan_id: int, new_name: str) -> bool:
        """Change the name of a VLAN."""
        try:
            commands = [
                f"vlan {vlan_id}",
                f"name {new_name}",
            ]
            self.device_handler.send_config_set(commands)
            # Clear VLAN cache asynchronously
            threading.Thread(target=self._clear_vlan_cache_async).start()
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error changing VLAN {vlan_id} name to {new_name}: {e}")
            return False