from .base import BaseLldp
from typing import List, Dict, Any, Union

class CiscoIosLldp(BaseLldp):
    """Cisco IOS implementation of LLDP features."""

    def get_lldp_neighbors(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show lldp neighbors"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting LLDP neighbors: {e}")
            return ""
