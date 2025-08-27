from .base import BaseArp
from typing import List, Dict, Any, Union

class CiscoIosArp(BaseArp):
    """Cisco IOS implementation of ARP features."""

    def get_arp_interface(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show arp interface"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting ARP interface: {e}")
            return ""

    def get_ip_arp(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show ip arp"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting IP ARP: {e}")
            return ""
