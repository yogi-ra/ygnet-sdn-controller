from .base import BaseVlans
from typing import List, Dict, Any

class UbiquitiEdgeSwitchVlans(BaseVlans):
    """Ubiquiti EdgeSwitch implementation of VLAN features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

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
        # VTP is Cisco-specific, not applicable to Ubiquiti
        # Return empty list as placeholder
        return []

    def get_vlan_config(self) -> List[Dict[str, Any]]:
        try:
            command = "show running-config | include vlan"
            raw_output = self.device_handler.send_command(command)
            # Simple parsing for VLAN configuration lines
            vlan_configs = []
            for line in raw_output.splitlines():
                if line.strip().startswith("vlan"):
                    vlan_configs.append({"config": line.strip()})
            return vlan_configs
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VLAN config: {e}")
            return []
            
    def get_vlan_membership(self, vlan_id: str) -> List[Dict[str, Any]]:
        try:
            command = f"show vlan id {vlan_id}"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VLAN membership for VLAN {vlan_id}: {e}")
            return []
            
    def create_vlan(self, vlan_id: str, vlan_name: str = None) -> bool:
        """
        Create a new VLAN on the device.
        
        Args:
            vlan_id: ID of the VLAN to create
            vlan_name: Optional name for the VLAN
            
        Returns:
            True if VLAN was created successfully, False otherwise
        """
        try:
            commands = [
                ["configure", "#"],
                [f"vlan {vlan_id}", "#"]
            ]
            
            if vlan_name:
                commands.append([f"name {vlan_name}", "#"])
                
            commands.extend([
                ["exit", "#"],
                ["exit", "#"]
            ])
            
            self.device_handler.send_multiline_commands(commands)
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error creating VLAN {vlan_id}: {e}")
            return False
            
    def delete_vlan(self, vlan_id: str) -> bool:
        """
        Delete a VLAN from the device.
        
        Args:
            vlan_id: ID of the VLAN to delete
            
        Returns:
            True if VLAN was deleted successfully, False otherwise
        """
        try:
            commands = [
                ["configure", "#"],
                [f"no vlan {vlan_id}", "#"],
                ["exit", "#"]
            ]
            
            self.device_handler.send_multiline_commands(commands)
            return True
        except Exception as e:
            self.device_handler.logger.error(f"Error deleting VLAN {vlan_id}: {e}")
            return False