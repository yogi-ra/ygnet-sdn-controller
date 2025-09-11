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
                    cls._instance._connection_queues = {}  # device_key -> queue of waiting requests
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
        
        # Ensure we have a lock and queue for this device
        if device_key not in self._connection_locks:
            self._connection_locks[device_key] = threading.Lock()
        if device_key not in self._connection_queues:
            self._connection_queues[device_key] = queue.Queue()

        # Check if we've reached the maximum connections for this device
        with self._connection_locks[device_key]:
            if self._connection_counts[device_key] >= self._max_connections_per_device:
                # Put the request in the queue and wait for a connection to be released
                q = self._connection_queues[device_key]
                # Create an event to signal when a connection is available
                connection_available = threading.Event()
                q.put(connection_available)
                # Wait for a connection to be released
                connection_available.wait()
                # After being notified, check again if we can create a connection
                if self._connection_counts[device_key] >= self._max_connections_per_device:
                    # If we still can't create a connection, put the event back in the queue
                    q.put(connection_available)
                    raise DeviceUnreachableError(f"Maximum connections ({self._max_connections_per_device}) reached for device {device_key}")

        # Try to reuse an existing connection or create a new one
        with self._connection_locks[device_key]:
            # Check if we have an existing connection we can reuse
            if device_key in self._connections and self._connections[device_key]:
                # Try to find a live connection
                for i, connection in enumerate(self._connections[device_key]):
                    try:
                        # Attempt a simple command to check if the connection is still live
                        connection.find_prompt()
                        print(f"Reusing existing connection to {device_info.ip_address}.")
                        return connection
                    except Exception as e:
                        print(f"Cached connection to {device_info.ip_address} is stale: {e}. Removing...")
                        # Remove stale connection
                        try:
                            connection.disconnect()
                        except:
                            pass
                        finally:
                            self._connections[device_key].pop(i)
                            self._connection_counts[device_key] -= 1

            # Establish a new connection
            try:
                # Perform a quick TCP port check before attempting full Netmiko connection
                print(f"Checking TCP port {device_info.port} on {device_info.ip_address}...")
                if not self._check_tcp_port_open(device_info.ip_address, device_info.port):
                    raise DeviceUnreachableError(f"TCP connection to device {device_info.ip_address}:{device_info.port} failed. Port may be closed or device unreachable.")
                
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
                
                # Add the new connection to our pool
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
        with self._connection_locks[device_key]:
            if device_key in self._connections:
                try:
                    # Try to find and remove the connection from our pool
                    if connection in self._connections[device_key]:
                        self._connections[device_key].remove(connection)
                        self._connection_counts[device_key] -= 1
                        
                        # Notify the next waiting request that a connection is available
                        if device_key in self._connection_queues and not self._connection_queues[device_key].empty():
                            try:
                                next_request = self._connection_queues[device_key].get_nowait()
                                next_request.set()
                            except queue.Empty:
                                pass
                except Exception as e:
                    print(f"Error releasing connection for {device_key}: {e}")

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
