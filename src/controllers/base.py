from typing import List, Dict, Any, Union, Tuple
from abc import ABC, abstractmethod
import logging
from concurrent.futures import TimeoutError

from netmiko import NetmikoAuthenticationException

from ..connection_manager import ConnectionManager
from ..device_info import DeviceConnectionInfo
from ..config import settings
from ..parsing_utils import parse_cli_output
from ..exceptions import (
    DeviceConnectionError,
    DeviceTimeoutError,
    DeviceAuthenticationError,
    DeviceError,
)

logger = logging.getLogger(__name__)

connection_manager = ConnectionManager()  # Get the singleton instance


class BaseDevice(ABC):
    """
    Base class for all device handlers. Manages SSH connections and generic command execution.
    This class is abstract and requires subclasses to define their netmiko_device_type.
    """

    def __init__(self, device_info: DeviceConnectionInfo):
        """
        Initializes the controller with device connection information.

        Args:
            device_info: A DeviceConnectionInfo object.
        """
        self.device_info = device_info
        self.connection = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def netmiko_device_type(self) -> str:
        """
        Abstract property to be implemented by subclasses, returning the Netmiko device_type string.
        """
        pass

    def connect(self) -> None:
        """
        Establishes an SSH connection to the device using the connection manager.
        """
        try:
            future = connection_manager.get_connection(
                self.device_info, self.netmiko_device_type
            )
            self.connection = future.result(
                timeout=settings.NETMIKO_TIMEOUT
            )  # Corrected timeout setting
            self.logger.info(
                f"Successfully connected to {self.device_info.ip_address}"  # Corrected to ip_address
            )
        except TimeoutError:
            self.logger.error(
                f"Connection to {self.device_info.ip_address} timed out."  # Corrected to ip_address
            )
            raise DeviceTimeoutError(
                f"Connection to {self.device_info.ip_address} timed out."  # Corrected to ip_address
            )
        except NetmikoAuthenticationException:  # Catch NetmikoAuthenticationException
            self.logger.error(
                f"Authentication failed for {self.device_info.ip_address}."  # Corrected to ip_address
            )
            raise DeviceAuthenticationError(
                f"Authentication failed for {self.device_info.ip_address}."  # Corrected to ip_address
            )
        except Exception as e:
            self.logger.error(
                f"Failed to connect to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )
            raise DeviceConnectionError(
                f"Failed to connect to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )

    def disconnect(self):
        """
        Does not close the SSH connection to allow for reuse.
        The connection manager handles the lifecycle.
        """
        pass

    def __enter__(self):
        """
        Context manager entry point. Establishes connection.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Does not close connection.
        """
        self.disconnect()

    def send_command(self, command: str, **kwargs) -> str:
        """
        Sends a single command to the device.
        """
        if not self.connection:
            self.connect()
        try:
            # Ensure we are in privileged EXEC mode before sending the command
            if not self.connection.check_enable_mode():
                self.connection.enable()
            output = self.connection.send_command(command, **kwargs)
            self.logger.debug(f"Raw output from Netmiko for command '{command}':\n{output}")
            return output
        except Exception as e:
            self.logger.error(
                f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )
            raise DeviceError(
                f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )

    def send_config_set(self, commands: List[str], **kwargs) -> str:
        """
        Sends a list of configuration commands to the device.
        """
        if not self.connection:
            self.connect()
        try:
            # Ensure we are in privileged EXEC mode before sending the command
            if not self.connection.check_enable_mode():
                self.connection.enable()
            output = self.connection.send_config_set(commands, **kwargs)
            self.logger.debug(f"Raw output from Netmiko for config commands '{commands}':\n{output}")
            return output
        except Exception as e:
            self.logger.error(
                f"Failed to send config commands '{commands}' to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )
            raise DeviceError(
                f"Failed to send config commands '{commands}' to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )

    def send_multiline_commands(self, command_patterns: List[List[str]]) -> str:
        """
        Sends multiple commands to the device, handling additional prompts based on patterns.
        """
        if not self.connection:
            self.connect()

        try:
            output = self.connection.send_multiline(command_patterns)
            self.logger.debug(
                f"Raw output from Netmiko for multiline commands: {command_patterns}\n{output}"
            )
            return output
        except Exception as e:
            self.logger.error(
                f"Failed to send multiline commands to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )
            raise DeviceError(
                f"Failed to send multiline commands to {self.device_info.ip_address}: {e}"  # Corrected to ip_address
            )

    def parse_cli_output(
        self,
        command: str,
        raw_output: str,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parses CLI output using the utility function.
        """
        return parse_cli_output(
            command,
            raw_output,
            self.device_info.device_type,
            self.netmiko_device_type,
        )
     
    def invalidate_feature_cache(self, feature_name: str) -> None:
        """
        Invalidates the cache for a specific feature by calling the API endpoint.
        This method should be called after configuration changes to ensure fresh data.
        """
        try:
            import requests
            import os
            
            # Get API base URL from environment or use default
            api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            
            # Construct the cache clear endpoint URL
            cache_clear_url = f"{api_base_url}/api/devices/{self.device_info.id}/cache/clear"
            
            # Prepare the request data
            cache_clear_data = {
                "prefixes": [f"device:{self.device_info.id}:features:{feature_name}"]
            }
            
            # Make the request to clear the cache
            response = requests.post(
                cache_clear_url,
                json=cache_clear_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                self.logger.info(f"Successfully invalidated cache for feature: {feature_name}")
            else:
                self.logger.warning(f"Failed to invalidate cache for feature: {feature_name}. Status code: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error invalidating cache for feature {feature_name}: {e}")