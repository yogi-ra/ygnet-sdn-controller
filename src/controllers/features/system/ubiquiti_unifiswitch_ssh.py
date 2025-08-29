from src.controllers.features.system.base import BaseSystem
from typing import List, Dict, Any
import re

class UbiquitiEdgeSwitchSSHSystem(BaseSystem):
    """Ubiquiti Unifi Switch SSH implementation of system features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    def get_version_info(self) -> Dict[str, Any]:
        try:
            command = "show version"
            raw_output = self.device_handler.send_command(command)
            parsed_output = self.device_handler.parse_cli_output(command, raw_output)
            
            # If parsing didn't work, we'll try to extract information manually
            if not parsed_output:
                version_info = {}
                for line in raw_output.splitlines():
                    if "Version" in line:
                        version_info["version"] = line.split(":")[1].strip()
                    elif "Build" in line:
                        version_info["build"] = line.split(":")[1].strip()
                    elif "HW" in line:
                        version_info["hardware"] = line.split(":")[1].strip()
                return version_info
            
            return parsed_output[0] if isinstance(parsed_output, list) and parsed_output else {}
        except Exception as e:
            self.device_handler.logger.error(f"Error getting version info: {e}")
            return {}
