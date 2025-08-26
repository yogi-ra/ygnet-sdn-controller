from typing import List, Dict, Any, Union
from abc import ABC, abstractmethod
import logging

from src.connection_manager import connection_manager
from src.device_info import DeviceConnectionInfo
from src.config import settings # Import settings

logger = logging.getLogger(__name__)

from ..parsing_utils import parse_cli_output

from ..exceptions import (
    DeviceConnectionError,
)


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
        self.logger = logging.getLogger(self.__class__.__name__)  # Initialize logger

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
        self.connection = connection_manager.get_connection(
            self.device_info, self.netmiko_device_type
        )

    def disconnect(self):
        """
        Does not close the SSH connection to allow for reuse.
        The connection manager handles the lifecycle.
        """
        pass  # We no longer disconnect here

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

    def send_command(self, command: str, read_timeout: int = settings.NETMIKO_READ_TIMEOUT) -> str:
        """
        Sends a single command to the device.
        """
        if not self.connection:
            raise DeviceConnectionError("Error: Not connected to any device.")
        output = self.connection.send_command(command, read_timeout=read_timeout)
        logger.debug(f"Raw output from Netmiko for command '{command}':\n{output}")
        return output

    def send_multiline_commands(self, command_patterns: List[List[str]]) -> str:
        """
        Sends multiple commands to the device, handling additional prompts based on patterns.
        """
        if not self.connection:
            raise DeviceConnectionError("Error: Not connected to any device.")
        output = self.connection.send_multiline(command_patterns)
        logger.debug(
            f"Raw output from Netmiko for multiline commands: {command_patterns}\n{output}"
        )
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

    def check_reachability(self) -> bool:
        try:
            # Attempt to get a connection. If successful, the device is reachable.
            # The connection manager handles caching, so this won't create a new connection every time.
            connection_manager.get_connection(self.device_info, self.netmiko_device_type)
            return True
        except Exception as e:
            self.logger.debug(f"Device {self.device_info.ip_address} is not reachable: {e}")
            return False
