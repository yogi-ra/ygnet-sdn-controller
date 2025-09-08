import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from src.config import settings
from src.device_info import DeviceConnectionInfo

# Mapping from our internal device types to Netmiko device types
NETMIKO_DEVICE_TYPE_MAP = {
    "cisco_ios_router": "cisco_ios",
    "cisco_ios_switch": "cisco_ios",
    "aruba_procurve": "hp_procurve",
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
                    cls._instance._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER_THREADS)
                    cls._instance._executor_shutdown = False
        return cls._instance

    def _connect_device(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Establishes a Netmiko connection to the device."""
        device_key = device_info.get_key()
        if device_key not in self._connection_locks:
            self._connection_locks[device_key] = threading.Lock()

        with self._connection_locks[device_key]:
            # Check if connection exists and is still alive
            if device_key in self._connections:
                connection = self._connections[device_key]
                try:
                    # Attempt a simple command to check if the connection is still live
                    connection.find_prompt()
                    print(f"Connection to {device_info.ip_address} is still live.")
                    return connection
                except Exception as e:
                    print(f"Cached connection to {device_info.ip_address} is stale: {e}. Reconnecting...")
                    # Remove stale connection
                    try:
                        connection.disconnect()
                    except:
                        pass
                    finally:
                        if device_key in self._connections:
                            del self._connections[device_key]

            # Establish a new connection
            try:
                print(f"Attempting to connect to {device_info.ip_address}...")
                # Use the mapped Netmiko device type
                netmiko_type = NETMIKO_DEVICE_TYPE_MAP.get(device_info.device_type, device_info.device_type)
                connection = ConnectHandler(
                    device_type=netmiko_type,
                    host=device_info.ip_address,
                    username=device_info.username,
                    password=device_info.password,
                    secret=device_info.secret,
                    port=device_info.port,
                    timeout=settings.NETMIKO_TIMEOUT,
                    global_delay_factor=0.5,
                    fast_cli=True,
                )
                self._connections[device_key] = connection
                print(f"Successfully connected to {device_info.ip_address}.")
                return connection
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                print(f"Connection failed for {device_info.ip_address}: {e}")
                if device_key in self._connections:
                    del self._connections[device_key]
                raise
            except Exception as e:
                print(f"An unexpected error occurred during connection to {device_info.ip_address}: {e}")
                if device_key in self._connections:
                    del self._connections[device_key]
                raise

    def get_connection(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Submits a connection request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
        return self._executor.submit(self._connect_device, device_info, netmiko_device_type)

    def send_command(self, device_info: DeviceConnectionInfo, command: str, netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a command execution request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_command():
            connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing command '{command}' on {device_info.ip_address}...")
                # Set a timeout for the command execution
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_command(command, read_timeout=cmd_timeout, **kwargs)
                print(f"Command '{command}' executed on {device_info.ip_address}.")
                return output
            except Exception as e:
                print(f"Error executing command '{command}' on {device_info.ip_address}: {e}")
                raise

        return self._executor.submit(_execute_command)

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a config set execution request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_config_set():
            connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing config commands on {device_info.ip_address}...")
                # Set a timeout for the command execution
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_config_set(commands, cmd_timeout=cmd_timeout, **kwargs)
                print(f"Config commands executed on {device_info.ip_address}.")
                return output
            except Exception as e:
                print(f"Error executing config commands on {device_info.ip_address}: {e}")
                raise

        return self._executor.submit(_execute_config_set)

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a multiline command execution request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_multiline_commands():
            connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
            try:
                # Ensure we are in privileged EXEC mode before sending the command
                if not connection.check_enable_mode():
                    connection.enable()
                print(f"Executing multiline commands on {device_info.ip_address}...")
                # Set a timeout for the command execution
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_multiline(command_patterns, read_timeout=cmd_timeout, **kwargs)
                print(f"Multiline commands executed on {device_info.ip_address}.")
                return output
            except Exception as e:
                print(f"Error executing multiline commands on {device_info.ip_address}: {e}")
                raise

        return self._executor.submit(_execute_multiline_commands)

    def disconnect_all(self):
        """
        Disconnects all active Netmiko connections.
        """
        with self._lock:
            for device_key, connection in list(self._connections.items()):
                try:
                    connection.disconnect()
                    print(f"Disconnected from {device_key}.")
                except Exception as e:
                    print(f"Error disconnecting from {device_key}: {e}")
                finally:
                    del self._connections[device_key]
            
            # Only shutdown if not already shutdown
            if not self._executor_shutdown:
                self._executor.shutdown(wait=True)
                self._executor_shutdown = True
            print("All connections disconnected and executor shut down.")