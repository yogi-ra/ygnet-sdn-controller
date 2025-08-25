from .base import BaseAcls
from typing import List, Dict, Any, Union

class CiscoIosAcls(BaseAcls):
    """Cisco IOS implementation of ACL features."""

    def get_acls(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | section access-list"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting ACLs: {e}")
            return ""
