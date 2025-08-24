from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

from src.parsing_utils import parse_cli_output  # New import

from ..exceptions import (
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceConnectionError,
)


@dataclass
class DeviceConnectionInfo:
    """
    Represents the connection details for a network device.
    This dataclass holds the raw information retrieved from the database.
    """

    ip_address: str
    device_type: str  # Our internal granular type (e.g., cisco_ios, juniper_junos)
    username: str
    password: str
    port: int = 22
    name: Optional[str] = None
    secret: Optional[str] = None


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

    @property
    @abstractmethod
    def netmiko_device_type(self) -> str:
        """
        Abstract property to be implemented by subclasses, returning the Netmiko device_type string.
        """
        pass

    def connect(self) -> None:
        """
        Establishes an SSH connection to the device using its IP address.

        Raises:
            DeviceAuthenticationError: If authentication fails.
            DeviceTimeoutError: If the connection times out.
            DeviceConnectionError: For other connection errors.
        """
        try:
            self.connection = ConnectHandler(
                host=self.device_info.ip_address,
                username=self.device_info.username,
                password=self.device_info.password,
                port=self.device_info.port,  # Use the custom port
                device_type=self.netmiko_device_type,  # Use the abstract property
                secret=self.device_info.secret,
            )
            if self.device_info.secret:
                self.connection.enable()
        except NetmikoAuthenticationException as e:
            raise DeviceAuthenticationError(
                f"Authentication failed for {self.device_info.ip_address}: {e}"
            ) from e
        except NetmikoTimeoutException as e:
            raise DeviceTimeoutError(
                f"Connection timed out for {self.device_info.ip_address}: {e}"
            ) from e
        except Exception as e:
            raise DeviceConnectionError(
                f"Failed to connect to {self.device_info.ip_address}: {e}"
            ) from e

    def disconnect(self):
        """
        Closes the SSH connection.
        """
        if self.connection:
            self.connection.disconnect()

    def __enter__(self):
        """
        Context manager entry point. Establishes connection.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point. Closes connection.
        """
        self.disconnect()

    def send_command(self, command: str) -> str:
        """
        Sends a single command to the device.
        """
        if not self.connection:
            raise DeviceConnectionError("Error: Not connected to any device.")
        output = self.connection.send_command(command)
        logger.debug(f"Raw output from Netmiko for command '{command}':\n{output}")
        return output

    def send_multiline_commands(self, command_patterns: List[List[str]]) -> str:
        """
        Sends multiple commands to the device, handling additional prompts based on patterns.
        """
        if not self.connection:
            raise DeviceConnectionError("Error: Not connected to any device.")
        output = self.connection.send_multiline(command_patterns)
        logger.debug(f"Raw output from Netmiko for multiline commands: {command_patterns}\n{output}")
        return output

    def parse_cli_output(
        self, command: str, raw_output: str
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parses CLI output using the utility function.
        """
        return parse_cli_output(
            command, raw_output, self.device_info.device_type, self.netmiko_device_type
        )
