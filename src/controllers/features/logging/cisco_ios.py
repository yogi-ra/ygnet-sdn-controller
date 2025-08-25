from .base import BaseLogging
from typing import List, Dict, Any, Union

class CiscoIosLogging(BaseLogging):
    """Cisco IOS implementation of logging features."""

    def get_logging_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | include logging"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting logging config: {e}")
            return ""
