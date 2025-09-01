import threading
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from src.config import settings
from src.device_info import DeviceConnectionInfo # Corrected import

# Mapping from our internal device types to Netmiko device types
NETMIKO_DEVICE_TYPE_MAP = {
    "cisco_ios_router": "cisco_ios",
    "cisco_ios_switch": "cisco_ios",
    "aruba_procurve": "hp_procurve", # Assuming hp_procurve is the Netmiko type for Aruba Procurve
    "ubiquiti_unifiswitch": "ubiquiti_unifiswitch_ssh",
    # Add other mappings as needed
}

class ConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConnectionManager, cls).__new__(cls)
                    cls._instance._connections = {}
                    cls._instance._connection_locks = {}
                    cls._instance._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER_THREADS) # Corrected setting name
        return cls._instance

    def _connect_device(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Establishes a Netmiko connection to the device."""
        device_key = device_info.get_key()
        if device_key not in self._connection_locks:
            self._connection_locks[device_key] = threading.Lock()

        with self._connection_locks[device_key]:
            # Removed is_alive() check as Netmiko connection objects don't have it
            if device_key not in self._connections:
                try:
                    print(f"Attempting to connect to {device_info.ip_address}...") # Corrected to ip_address
                    # Use the mapped Netmiko device type
                    netmiko_type = NETMIKO_DEVICE_TYPE_MAP.get(device_info.device_type, device_info.device_type)
                    connection = ConnectHandler(
                        device_type=netmiko_type, # Use the mapped type here
                        host=device_info.ip_address, # Corrected to ip_address
                        username=device_info.username,
                        password=device_info.password,
                        secret=device_info.secret,
                        port=device_info.port,
                        timeout=settings.NETMIKO_TIMEOUT # Corrected setting name
                    )
                    self._connections[device_key] = connection
                    print(f"Successfully connected to {device_info.ip_address}.") # Corrected to ip_address
                except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                    print(f"Connection failed for {device_info.ip_address}: {e}") # Corrected to ip_address
                    if device_key in self._connections:
                        del self._connections[device_key]
                    raise
                except Exception as e:
                    print(f"An unexpected error occurred during connection to {device_info.ip_address}: {e}") # Corrected to ip_address
                    if device_key in self._connections:
                        del self._connections[device_key]
                    raise
            else:
                # Connection exists, perform a liveness check
                connection = self._connections[device_key]
                try:
                    # Attempt a simple command to check if the connection is still live
                    connection.find_prompt()
                    print(f"Connection to {device_info.ip_address} is still live.")
                except Exception as e:
                    print(f"Cached connection to {device_info.ip_address} is stale: {e}. Reconnecting...")
                    if device_key in self._connections:
                        del self._connections[device_key] # Remove stale connection
                    # Re-raise to force a new connection attempt in the next iteration
                    raise # Re-raise the exception to trigger a new connection attempt
            return self._connections[device_key]

    def get_connection(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Submits a connection request to the thread pool and returns a Future."""
        return self._executor.submit(self._connect_device, device_info, netmiko_device_type)

    def send_command(self, device_info: DeviceConnectionInfo, command: str, netmiko_device_type: str, **kwargs):
        """Submits a command execution request to the thread pool and returns a Future."""
        def _execute_command():
            connection = self._connect_device(device_info, netmiko_device_type) # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing command '{command}' on {device_info.ip_address}...") # Corrected to ip_address
                output = connection.send_command(command, **kwargs)
                print(f"Command '{command}' executed on {device_info.ip_address}.") # Corrected to ip_address
                return output
            except Exception as e:
                print(f"Error executing command '{command}' on {device_info.ip_address}: {e}") # Corrected to ip_address
                raise

        return self._executor.submit(_execute_command)

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, **kwargs):
        """Submits a config set execution request to the thread pool and returns a Future."""
        def _execute_config_set():
            connection = self._connect_device(device_info, netmiko_device_type) # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing config commands '{commands}' on {device_info.ip_address}...") # Corrected to ip_address
                output = connection.send_config_set(commands, **kwargs)
                print(f"Config commands '{commands}' executed on {device_info.ip_address}.") # Corrected to ip_address
                return output
            except Exception as e:
                print(f"Error executing config commands '{commands}' on {device_info.ip_address}: {e}") # Corrected to ip_address
                raise

        return self._executor.submit(_execute_config_set)

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, **kwargs):
        """Submits a multiline command execution request to the thread pool and returns a Future."""
        def _execute_multiline_commands():
            connection = self._connect_device(device_info, netmiko_device_type) # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing multiline commands '{command_patterns}' on {device_info.ip_address}...") # Corrected to ip_address
                output = connection.send_multiline(command_patterns, **kwargs)
                print(f"Multiline commands '{command_patterns}' executed on {device_info.ip_address}.") # Corrected to ip_address
                return output
            except Exception as e:
                print(f"Error executing multiline commands '{command_patterns}' on {device_info.ip_address}: {e}") # Corrected to ip_address
                raise

        return self._executor.submit(_execute_multiline_commands)

    def disconnect_all(self):
        """
        Disconnects all active Netmiko connections.
        """
        with self._lock:
            for device_key, connection in list(self._connections.items()):
                try:
                    # Removed is_alive() check
                    connection.disconnect()
                    print(f"Disconnected from {device_key}.")
                except Exception as e:
                    print(f"Error disconnecting from {device_key}: {e}")
                finally:
                    del self._connections[device_key]
            self._executor.shutdown(wait=True)
            print("All connections disconnected and executor shut down.")
