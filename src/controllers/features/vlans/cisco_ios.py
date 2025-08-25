from .base import BaseVlans
from typing import List, Dict, Any

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
