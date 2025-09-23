import threading
import socket
import queue
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from src.config import settings
from src.device_info import DeviceConnectionInfo
from src.exceptions import DeviceUnreachableError

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
                    cls._instance._connections = {}  # device_key -> [connection objects]
                    cls._instance._connection_locks = {}  # device_key -> lock
                    cls._instance._connection_counts = defaultdict(int)  # device_key -> count
                    cls._instance._max_connections_per_device = 2  # Default max connections per device
                    cls._instance._connection_conditions = {}  # device_key -> threading.Condition
                    cls._instance._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER_THREADS)
                    cls._instance._executor_shutdown = False
        return cls._instance

    def _check_tcp_port_open(self, ip_address: str, port: int, timeout: float = 2.0) -> bool:
        """
        Checks if a TCP port is open on a given IP address.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip_address, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
        finally:
            sock.close()

    def _connect_device(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Establishes a Netmiko connection to the device."""
        device_key = device_info.get_key()
        
        # Ensure we have a lock and condition for this device
        if device_key not in self._connection_locks:
            self._connection_locks[device_key] = threading.Lock()
        if device_key not in self._connection_conditions:
            # Use the existing lock for the condition
            self._connection_conditions[device_key] = threading.Condition(self._connection_locks[device_key])

        with self._connection_conditions[device_key]:
            while self._connection_counts[device_key] >= self._max_connections_per_device:
                print(f"Max connections reached for {device_key}. Waiting for a connection to be released...")
                self._connection_conditions[device_key].wait()

            # At this point, we have a slot.

            # Clean up stale connections and check for a reusable one
            if device_key in self._connections and self._connections[device_key]:
                # Iterate over a copy of the list to allow for safe removal
                for connection in list(self._connections[device_key]):
                    try:
                        if connection.is_alive():
                            print(f"Reusing existing connection to {device_info.ip_address}.")
                            return connection
                        else:
                            # This connection is stale, remove it from the pool
                            print(f"Stale connection found for {device_info.ip_address}. Removing...")
                            try:
                                connection.disconnect()
                            except Exception:
                                pass  # Ignore errors on disconnect
                            self._connections[device_key].remove(connection)
                            self._connection_counts[device_key] -= 1
                    except Exception as e:
                        # Handle cases where is_alive() itself throws an error
                        print(f"Error checking stale connection for {device_info.ip_address}: {e}. Removing...")
                        try:
                            connection.disconnect()
                        except Exception:
                            pass  # Ignore errors on disconnect
                        
                        # Ensure the connection is removed even if it was already gone
                        if connection in self._connections[device_key]:
                            self._connections[device_key].remove(connection)
                            self._connection_counts[device_key] -= 1

            # If no reusable connection, establish a new one
            print(f"Attempting to connect to {device_info.ip_address}...")
            try:
                # Perform a quick TCP port check
                if not self._check_tcp_port_open(device_info.ip_address, device_info.port):
                    raise DeviceUnreachableError(f"TCP connection to device {device_info.ip_address}:{device_info.port} failed.")
                
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
                
                if device_key not in self._connections:
                    self._connections[device_key] = []
                self._connections[device_key].append(connection)
                self._connection_counts[device_key] += 1
                
                print(f"Successfully connected to {device_info.ip_address}.")
                return connection
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                print(f"Connection failed for {device_info.ip_address}: {e}")
                raise
            except Exception as e:
                print(f"An unexpected error occurred during connection to {device_info.ip_address}: {e}")
                raise

    def _release_connection(self, device_info: DeviceConnectionInfo, connection):
        """Release a connection back to the pool."""
        device_key = device_info.get_key()
        with self._connection_conditions[device_key]:
            if device_key in self._connections and connection in self._connections[device_key]:
                self._connections[device_key].remove(connection)
                self._connection_counts[device_key] -= 1
                # Notify one waiting thread that a connection is available
                self._connection_conditions[device_key].notify()

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
            connection = None
            try:
                connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
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
            finally:
                # Always release the connection back to the pool
                if connection:
                    self._release_connection(device_info, connection)

        return self._executor.submit(_execute_command)

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a config set execution request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_config_set():
            connection = None
            try:
                connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
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
            finally:
                # Always release the connection back to the pool
                if connection:
                    self._release_connection(device_info, connection)

        return self._executor.submit(_execute_config_set)

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a multiline command execution request to the thread pool and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_multiline_commands():
            connection = None
            try:
                connection = self._connect_device(device_info, netmiko_device_type)  # Ensure connection is active or re-established
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
            finally:
                # Always release the connection back to the pool
                if connection:
                    self._release_connection(device_info, connection)

        return self._executor.submit(_execute_multiline_commands)

    def set_max_connections_per_device(self, max_connections: int):
        """Set the maximum number of concurrent connections per device."""
        self._max_connections_per_device = max_connections

    def get_connection_count(self, device_info: DeviceConnectionInfo) -> int:
        """Get the current number of active connections for a device."""
        device_key = device_info.get_key()
        return self._connection_counts[device_key]

    def disconnect_all(self):
        """
        Disconnects all active Netmiko connections.
        """
        with self._lock:
            for device_key, connections in list(self._connections.items()):
                for connection in connections:
                    try:
                        connection.disconnect()
                        print(f"Disconnected from {device_key}.")
                    except Exception as e:
                        print(f"Error disconnecting from {device_key}: {e}")
                # Clear the connection list for this device
                self._connections[device_key] = []
                self._connection_counts[device_key] = 0
                
                # Clear the queue for this device
                if device_key in self._connection_queues:
                    while not self._connection_queues[device_key].empty():
                        try:
                            event = self._connection_queues[device_key].get_nowait()
                            event.set()  # Release waiting threads
                        except queue.Empty:
                            break
                    del self._connection_queues[device_key]
            
            # Only shutdown if not already shutdown
            if not self._executor_shutdown:
                self._executor.shutdown(wait=True)
                self._executor_shutdown = True
            print("All connections disconnected and executor shut down.")
