from typing import List, Dict, Any, Union
from abc import ABC, abstractmethod
import logging
from concurrent.futures import TimeoutError
from netmiko import (
    NetmikoAuthenticationException,
)  # Import NetmikoAuthenticationException

from src.connection_manager import ConnectionManager

connection_manager = ConnectionManager() # Get the singleton instance
from src.device_info import DeviceConnectionInfo
from src.config import settings

logger = logging.getLogger(__name__)

from ..parsing_utils import parse_cli_output

from ..exceptions import (
    DeviceConnectionError,
    DeviceTimeoutError,
    DeviceAuthenticationError,
    DeviceError,
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
            future = connection_manager.get_connection(self.device_info, self.netmiko_device_type)
            self.connection = future.result(
                timeout=settings.NETMIKO_TIMEOUT
            )  # Corrected timeout setting
            self.logger.info(
                f"Successfully connected to {self.device_info.ip_address}"
            )  # Corrected to ip_address
        except TimeoutError:
            self.logger.error(
                f"Connection to {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
            raise DeviceTimeoutError(
                f"Connection to {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
        except NetmikoAuthenticationException:  # Catch NetmikoAuthenticationException
            self.logger.error(
                f"Authentication failed for {self.device_info.ip_address}."
            )  # Corrected to ip_address
            raise DeviceAuthenticationError(
                f"Authentication failed for {self.device_info.ip_address}."
            )  # Corrected to ip_address
        except Exception as e:
            self.logger.error(
                f"Failed to connect to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address
            raise DeviceConnectionError(
                f"Failed to connect to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address

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
        try:
            future = connection_manager.send_command(
                self.device_info, command, self.netmiko_device_type, **kwargs
            )
            output = future.result(
                timeout=settings.NETMIKO_TIMEOUT
            )  # Corrected timeout setting
            logger.debug(f"Raw output from Netmiko for command '{command}':\n{output}")
            return output
        except TimeoutError:
            self.logger.error(
                f"Command '{command}' on {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
            raise DeviceTimeoutError(
                f"Command '{command}' on {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
        except Exception as e:
            self.logger.error(
                f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address
            raise DeviceError(
                f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address

    def send_multiline_commands(self, command_patterns: List[List[str]]) -> str:
        """
        Sends multiple commands to the device, handling additional prompts based on patterns.
        """
        if not self.connection:
            # Re-establish connection if it's somehow lost, though connect() should handle this
            self.connect()

        try:
            # Netmiko's send_multiline is not directly exposed via connection_manager's send_command
            # as it's a more complex interaction. We ensure connection is active and use it directly.
            output = self.connection.send_multiline(command_patterns)
            logger.debug(
                f"Raw output from Netmiko for multiline commands: {command_patterns}\n{output}"
            )
            return output
        except TimeoutError:
            self.logger.error(
                f"Multiline command on {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
            raise DeviceTimeoutError(
                f"Multiline command on {self.device_info.ip_address} timed out."
            )  # Corrected to ip_address
        except Exception as e:
            self.logger.error(
                f"Failed to send multiline commands to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address
            raise DeviceError(
                f"Failed to send multiline commands to {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address

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
            future = connection_manager.get_connection(self.device_info, self.netmiko_device_type)
            # We don't need to store the connection, just check if it can be established
            future.result(timeout=settings.NETMIKO_TIMEOUT)  # Corrected timeout setting
            return True
        except (
            TimeoutError,
            DeviceConnectionError,
            NetmikoAuthenticationException,
        ) as e:  # Catch NetmikoAuthenticationException
            self.logger.debug(
                f"Device {self.device_info.ip_address} is not reachable: {e}"
            )  # Corrected to ip_address
            return False
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred while checking reachability for {self.device_info.ip_address}: {e}"
            )  # Corrected to ip_address
            return False
