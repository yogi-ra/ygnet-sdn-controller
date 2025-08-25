from .base import BaseInterfaces
from typing import List, Dict, Any, Union

class CiscoIosInterfaces(BaseInterfaces):
    """Cisco IOS implementation of interface features."""

    def get_interfaces_brief(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip interface brief"
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
