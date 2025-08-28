from .base import BaseSystem
from typing import List, Dict, Any
import re


class CiscoIosSystem(BaseSystem):
    """Cisco IOS implementation of system features."""

    def get_version_info(self) -> List[Dict[str, Any]]:
        try:
            command = "show version"
            raw_output = self.device_handler.send_command(command)
            version_data = self.device_handler.parse_cli_output(command, raw_output)
            if version_data and isinstance(version_data, list):
                return version_data  # Return the list directly
        except Exception as e:
            self.device_handler.logger.error(f"Error getting version info: {e}")
        return [] # Return an empty list if no data or error

    def get_hostname(self) -> str:
        version_info = self.get_version_info()
        if version_info and isinstance(version_info, list) and len(version_info) > 0 and isinstance(version_info[0], dict):
            return version_info[0].get("hostname", "")
        return "" # Return empty string if hostname not found or version_info is not as expected

    def get_uptime(self) -> str:
        try:
            command = "show version"
            raw_output = self.device_handler.send_command(command)
            match = re.search(r"uptime is (.*)", raw_output)
            if match:
                return match.group(1).strip()
            return "N/A"
        except Exception as e:
            self.device_handler.logger.error(f"Error getting uptime: {e}")
            return f"Error: {e}"

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

                    match = re.search(r"privilege\s+(\d+)", line)
                    if match:
                        user_data["privilege"] = match.group(1)

                    results.append(user_data)

            return results
        except Exception as e:
            self.device_handler.logger.error(f"Error getting local users: {e}")
            return []

    def get_clock(self) -> str:
        try:
            output = self.device_handler.send_command(command="show clock")
            if output.startswith("*"):
                output = output[1:].strip()
            return output
        except Exception as e:
            self.device_handler.logger.error(f"Error getting clock: {e}")
            return f"Error: {e}"

    def reload_device(self, save_config: bool = True) -> str:
        try:
            if save_config:
                self.device_handler.send_command("write memory") # Save config before reload
            
            output = self.device_handler.send_command_timing("reload")
            if "Proceed with reload?" in output:
                output += self.device_handler.send_command_timing("y") # Confirm reload
            
            return f"Device reload initiated: {output}"
        except Exception as e:
            self.device_handler.logger.error(f"Error reloading device: {e}")
            raise
