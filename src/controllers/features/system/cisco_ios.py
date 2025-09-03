from .base import BaseSystem
from typing import List, Dict, Any


class CiscoIosSystem(BaseSystem):
    """Cisco IOS implementation of system features."""

    def get_version_info(self) -> List[Dict[str, Any]]:
        try:
            command = "show version"
            raw_output = self.device_handler.send_command(command)
            parsed_output = self.device_handler.parse_cli_output(command, raw_output)
            return parsed_output if isinstance(parsed_output, list) else [parsed_output]
        except Exception as e:
            self.device_handler.logger.error(f"Error getting version info: {e}")
            return []

    def get_hostname(self) -> str:
        try:
            # Try to get hostname from prompt first
            prompt = self.device_handler.connection.find_prompt()
            if prompt and '#' in prompt:
                return prompt.split('#')[0]
            elif prompt and '>' in prompt:
                return prompt.split('>')[0]
            
            # Fallback to show running-config
            command = "show running-config | include hostname"
            raw_output = self.device_handler.send_command(command)
            if raw_output and "hostname" in raw_output:
                return raw_output.split()[1].strip()
            return "Unknown"
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
            # Parse from show version output
            version_info = self.get_version_info()
            if version_info and len(version_info) > 0:
                # Look for uptime in the version info
                version_data = version_info[0]
                if "uptime" in version_data:
                    return version_data["uptime"]
                elif "system_up_time" in version_data:
                    return version_data["system_up_time"]
            return "Unknown"
        except Exception as e:
            self.device_handler.logger.error(f"Error getting uptime: {e}")
            return "Unknown"

    def reboot(self) -> str:
        """
        Reboot the device.
        """
        try:
            # Send reload command with confirmation
            output = self.device_handler.connection.send_command_timing("reload")
            if "confirm" in output.lower():
                output += self.device_handler.connection.send_command_timing("\n")
            return output
        except Exception as e:
            self.device_handler.logger.error(f"Error rebooting device: {e}")
            return str(e)