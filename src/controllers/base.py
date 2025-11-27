from typing import List, Dict, Any, Union, Tuple
from abc import ABC, abstractmethod
import logging
from concurrent.futures import TimeoutError as FutureTimeoutError

from netmiko import NetmikoAuthenticationException, ConnectHandler

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

# Mapping from our internal device types to Netmiko device types
NETMIKO_DEVICE_TYPE_MAP = {
    "cisco_ios_router": "cisco_ios",
    "cisco_ios_switch": "cisco_ios",
    "aruba_procurve": "hp_procurve",
    "ubiquiti_unifiswitch": "ubiquiti_unifiswitch_ssh",
}

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
        self._connection_established = False  # Track if we have an active connection

    @property
    @abstractmethod
    def netmiko_device_type(self) -> str:
        """
        Abstract property to be implemented by subclasses, returning the Netmiko device_type string.
        """
        pass

    def connect(self) -> None:
        """
        Establishes an SSH connection to the device using direct Netmiko for performance.
        """
        if self._connection_established and self.connection and self.connection.is_alive():
            return  # Already connected

        try:
            netmiko_type = NETMIKO_DEVICE_TYPE_MAP.get(self.device_info.device_type, self.device_info.device_type)

            # Enhanced connection parameters for better performance
            connection_params = {
                'device_type': netmiko_type,
                'host': self.device_info.ip_address,
                'username': self.device_info.username,
                'password': self.device_info.password,
                'secret': self.device_info.secret,
                'port': self.device_info.port,
                'timeout': settings.NETMIKO_TIMEOUT,
                'session_timeout': settings.NETMIKO_TIMEOUT + 10,
                'fast_cli': True,  # Enable fast_cli for better performance
            }

            # Add optional parameters if they exist in settings
            if hasattr(settings, 'NETMIKO_BANNER_TIMEOUT'):
                connection_params['banner_timeout'] = settings.NETMIKO_BANNER_TIMEOUT

            self.connection = ConnectHandler(**connection_params)

            # Verify connection is responsive
            self.connection.send_command("\n", read_timeout=5)

            self._connection_established = True
            self.logger.info(f"Successfully connected to {self.device_info.ip_address}")
        except NetmikoAuthenticationException:
            self.logger.error(f"Authentication failed for {self.device_info.ip_address}.")
            raise DeviceAuthenticationError(f"Authentication failed for {self.device_info.ip_address}.")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.device_info.ip_address}: {e}")
            raise DeviceConnectionError(f"Failed to connect to {self.device_info.ip_address}: {e}")

    def disconnect(self):
        """
        Closes the SSH connection.
        """
        if self.connection and self._connection_established:
            try:
                self.connection.disconnect()
                self._connection_established = False
                self.connection = None
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")

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

    def send_command(self, command: str, timeout: int = None, **kwargs) -> str:
        """
        Sends a single command to the device using direct connection for performance.
        """
        if not self.connection or not self._connection_established:
            self.connect()

        try:
            # Ensure we are in privileged EXEC mode before sending the command
            if not self.connection.check_enable_mode():
                self.connection.enable()

            # Set a reasonable timeout for command execution
            cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
            output = self.connection.send_command(command, read_timeout=cmd_timeout, **kwargs)
            self.logger.debug(f"Raw output from Netmiko for command '{command}':\n{output}")
            return output
        except Exception as e:
            self.logger.error(f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}")
            # Attempt to reestablish connection if command failed
            self._connection_established = False
            self.connection = None
            raise DeviceError(f"Failed to send command '{command}' to {self.device_info.ip_address}: {e}")

    def send_config_set(self, commands: List[str], timeout: int = None, **kwargs) -> str:
        """
        Sends a list of configuration commands to the device, ensuring proper mode transitions.
        """
        if not self.connection or not self._connection_established:
            self.connect()

        try:
            # Ensure we are in privileged EXEC mode
            if not self.connection.check_enable_mode():
                self.connection.enable()

            # Set a reasonable timeout for command execution
            cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
            # Netmiko's send_config_set handles entering and exiting config mode by default
            output = self.connection.send_config_set(commands, read_timeout=cmd_timeout, exit_config_mode=True, **kwargs)

            self.logger.debug(f"Raw output from Netmiko for config commands '{commands}':\n{output}")
            return output
        except Exception as e:
            # Attempt to exit config mode only if we are currently in it
            try:
                if self.connection.check_config_mode():
                    self.connection.exit_config_mode()
            except Exception as exit_e:
                self.logger.error(f"Error attempting to exit config mode: {exit_e}")

            self.logger.error(f"Failed to send config commands '{commands}' to {self.device_info.ip_address}: {e}")
            # Attempt to reestablish connection if command failed
            self._connection_established = False
            self.connection = None
            raise DeviceError(f"Failed to send config commands '{commands}' to {self.device_info.ip_address}: {e}")

    def send_multiline_commands(self, command_patterns: List[List[str]], timeout: int = None) -> str:
        """
        Sends multiple commands to the device, handling additional prompts based on patterns.
        """
        if not self.connection or not self._connection_established:
            self.connect()

        try:
            # Set a reasonable timeout for command execution
            cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
            output = self.connection.send_multiline(command_patterns, read_timeout=cmd_timeout)
            self.logger.debug(f"Raw output from Netmiko for multiline commands: {command_patterns}\n{output}")
            return output
        except Exception as e:
            self.logger.error(f"Failed to send multiline commands to {self.device_info.ip_address}: {e}")
            # Attempt to reestablish connection if command failed
            self._connection_established = False
            self.connection = None
            raise DeviceError(f"Failed to send multiline commands to {self.device_info.ip_address}: {e}")

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
     
    