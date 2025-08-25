import threading
from typing import Dict
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import logging

from src.device_info import DeviceConnectionInfo
from src.exceptions import (
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceConnectionError,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    _instance = None
    _lock = threading.Lock()
    _connections: Dict[str, ConnectHandler] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance

    def get_connection(self, device_info: DeviceConnectionInfo, netmiko_device_type: str) -> ConnectHandler:
        with self._lock:
            connection = self._connections.get(device_info.ip_address)

            if connection and self._is_connection_alive(connection):
                logger.info(f"Reusing existing connection to {device_info.ip_address}")
                return connection

            logger.info(f"Creating new connection to {device_info.ip_address}")
            try:
                new_connection = ConnectHandler(
                    host=device_info.ip_address,
                    username=device_info.username,
                    password=device_info.password,
                    port=device_info.port,
                    device_type=netmiko_device_type,
                    secret=device_info.secret,
                )
                if device_info.secret:
                    new_connection.enable()

                self._connections[device_info.ip_address] = new_connection
                return new_connection
            except NetmikoAuthenticationException as e:
                raise DeviceAuthenticationError(
                    f"Authentication failed for {device_info.ip_address}: {e}"
                ) from e
            except NetmikoTimeoutException as e:
                raise DeviceTimeoutError(
                    f"Connection timed out for {device_info.ip_address}: {e}"
                ) from e
            except Exception as e:
                raise DeviceConnectionError(
                    f"Failed to connect to {device_info.ip_address}: {e}"
                ) from e

    def _is_connection_alive(self, connection: ConnectHandler) -> bool:
        try:
            return connection.is_alive()
        except Exception:
            return False


# Singleton instance
connection_manager = ConnectionManager()