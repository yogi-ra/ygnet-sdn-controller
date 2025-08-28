from .base import BaseNtp
from typing import List, Dict, Any, Union

class CiscoIosNtp(BaseNtp):
    """Cisco IOS implementation of NTP features."""

    def get_ntp_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | include ntp"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting NTP config: {e}")
            return ""

    def set_ntp_server(self, ip_address: str) -> str:
        try:
            commands = [f"ntp server {ip_address}"]
            output = self.device_handler.send_config_set(commands)
            return f"NTP server {ip_address} configured: {output}"
        except Exception as e:
            self.device_handler.logger.error(f"Error setting NTP server: {e}")
            raise
