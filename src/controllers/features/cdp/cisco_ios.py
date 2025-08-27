from .base import BaseCDP
from typing import List, Dict, Any

class CiscoIosCdp(BaseCDP):
    """Abstract base class for cdp features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    def get_cdp_neighbors(self) -> List[Dict[str, Any]]:
        try:
            command = "show cdp neighbors"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting active users: {e}")
            return []
