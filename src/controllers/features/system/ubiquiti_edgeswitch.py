from src.controllers.features.system.base import BaseSystem
from typing import List, Dict, Any
import re

class UbiquitiEdgeSwitchSystem(BaseSystem):
    """Ubiquiti EdgeSwitch implementation of system features."""

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

    def get_hostname(self) -> str:
        try:
            command = "show running-config | include hostname"
            raw_output = self.device_handler.send_command(command)
            match = re.search(r"hostname\s+(.+)", raw_output)
            return match.group(1).strip() if match else "Unknown"
        except Exception as e:
            self.device_handler.logger.error(f"Error getting hostname: {e}")
            return "Unknown"

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
            command = "show running-config | include username"
            raw_output = self.device_handler.send_command(command)
            users = []
            for line in raw_output.splitlines():
                if line.strip().startswith("username"):
                    parts = line.split()
                    if len(parts) >= 2:
                        users.append({"username": parts[1]})
            return users
        except Exception as e:
            self.device_handler.logger.error(f"Error getting local users: {e}")
            return []

    def get_clock(self) -> str:
        try:
            command = "show clock"
            raw_output = self.device_handler.send_command(command)
            return raw_output.strip()
        except Exception as e:
            self.device_handler.logger.error(f"Error getting clock: {e}")
            return "Unknown"

    def get_uptime(self) -> str:
        try:
            command = "show version | include uptime"
            raw_output = self.device_handler.send_command(command)
            match = re.search(r"uptime is (.+)", raw_output)
            return match.group(1).strip() if match else "Unknown"
        except Exception as e:
            self.device_handler.logger.error(f"Error getting uptime: {e}")
            return "Unknown"