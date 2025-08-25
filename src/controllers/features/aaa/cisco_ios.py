from .base import BaseAaa
from typing import List, Dict, Any, Union

class CiscoIosAaa(BaseAaa):
    """Cisco IOS implementation of AAA features."""

    def get_aaa_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | section aaa"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting AAA config: {e}")
            return ""

    
