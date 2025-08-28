from .base import BaseSnmp
from typing import List, Dict, Any, Union

class CiscoIosSnmp(BaseSnmp):
    """Cisco IOS implementation of SNMP features."""

    def get_snmp_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | include snmp-server"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting SNMP config: {e}")
            return ""

    def toggle_snmp_service(self, enable: bool) -> str:
        try:
            if enable:
                commands = [
                    "snmp-server community public RO",
                    "snmp-server enable traps",
                ]
                output = self.device_handler.send_config_set(commands)
                return f"SNMP enabled: {output}"
            else:
                commands = [
                    "no snmp-server community public",
                    "no snmp-server enable traps",
                ]
                output = self.device_handler.send_config_set(commands)
                return f"SNMP disabled: {output}"
        except Exception as e:
            self.device_handler.logger.error(f"Error toggling SNMP service: {e}")
            raise
