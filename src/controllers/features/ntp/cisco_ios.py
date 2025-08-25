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
