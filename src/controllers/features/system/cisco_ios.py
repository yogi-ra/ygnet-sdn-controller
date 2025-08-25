from .base import BaseSystem
from typing import List, Dict, Any
from datetime import datetime
import re

class CiscoIosSystem(BaseSystem):
    """Cisco IOS implementation of system features."""

    def get_version_info(self) -> Dict[str, Any]:
        try:
            command = "show version"
            raw_output = self.device_handler.send_command(command)
            version_data = self.device_handler.parse_cli_output(command, raw_output)
            if version_data and isinstance(version_data, list):
                return version_data[0]
        except Exception as e:
            self.device_handler.logger.error(f"Error getting version info: {e}")
        return {}

    def get_hostname(self) -> str:
        version_info = self.get_version_info()
        return version_info.get("hostname", "")

    def get_active_users(self) -> List[Dict[str, Any]]:
        try:
            command = "show users"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting active users: {e}")
            return []

    def get_local_users(self) -> List[Dict[str, str]]:
        try:
            command = "show running-config | include ^username"
            output = self.device_handler.send_command(command=command)
            lines = output.strip().splitlines()

            results = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    username = parts[1]
                    user_data = {"username": username}

                    match = re.search(r'privilege\s+(\d+)', line)
                    if match:
                        user_data["privilege"] = match.group(1)

                    results.append(user_data)

            return results
        except Exception as e:
            self.device_handler.logger.error(f"Error getting local users: {e}")
            return []

    def get_clock(self) -> datetime:
        try:
            output = self.device_handler.send_command(command="show clock")
            if output.startswith("*"):
                output = output[1:].strip()
            return datetime.strptime(output, "%H:%M:%S.%f UTC %a %b %d %Y")
        except Exception as e: # Catch general Exception instead of just ValueError
            self.device_handler.logger.error(f"Error getting clock: {e}")
            return None # Return None on error
