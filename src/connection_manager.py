import threading
import socket
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from src.config import settings
from src.device_info import DeviceConnectionInfo
from src.exceptions import DeviceUnreachableError
from src.database import SessionLocal
from src.crud import crud
from src.schemas import DeviceUpdate

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
                    cls._instance._max_connections_per_device = 3  # Default max connections per device
                    cls._instance._connection_conditions = {}  # device_key -> threading.Condition
                    cls._instance._request_queues = {}  # device_key -> queue.Queue for pending requests
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
        if device_key not in self._request_queues:
            self._request_queues[device_key] = queue.Queue()

        with self._connection_conditions[device_key]:
            while self._connection_counts[device_key] >= self._max_connections_per_device:
                print(f"Max connections reached for {device_key}. Waiting for a connection to be released...")
                self._connection_conditions[device_key].wait()

            # At this point, we have a slot.

            # Clean up stale connections and check for a reusable one
            # Always perform a TCP port check before reusing a connection
            if device_key in self._connections and self._connections[device_key]:
                # Iterate over a copy of the list to allow for safe removal
                for connection in list(self._connections[device_key]):
                    try:
                        # Perform a TCP port check before considering the connection alive
                        if self._check_tcp_port_open(device_info.ip_address, device_info.port):
                            if self._validate_connection(connection):
                                print(f"Reusing existing connection to {device_info.ip_address}.")
                                return connection
                            else:
                                # This connection is stale, remove it from the pool
                                print(f"Stale connection found for {device_info.ip_address}. Removing...")
                                try:
                                    connection.disconnect()
                                except Exception as disconnect_error:
                                    print(f"Error disconnecting stale connection for {device_info.ip_address}: {disconnect_error}")
                                self._connections[device_key].remove(connection)
                                self._connection_counts[device_key] -= 1
                        else:
                            # Port is closed, mark device as unreachable and remove connection
                            print(f"Device {device_info.ip_address} port is closed. Removing connection.")
                            try:
                                connection.disconnect()
                            except Exception as disconnect_error:
                                print(f"Error disconnecting connection for unreachable device {device_info.ip_address}: {disconnect_error}")
                            self._connections[device_key].remove(connection)
                            self._connection_counts[device_key] -= 1
                            # Update database and invalidate cache when device is unreachable
                            self._update_device_reachability(device_info, False)
                    except Exception as e:
                        # Handle cases where is_alive() itself throws an error
                        print(f"Error checking stale connection for {device_info.ip_address}: {e}. Removing...")
                        try:
                            connection.disconnect()
                        except Exception as disconnect_error:
                            print(f"Error disconnecting problematic connection for {device_info.ip_address}: {disconnect_error}")
                        
                        # Ensure the connection is removed even if it was already gone
                        if connection in self._connections[device_key]:
                            self._connections[device_key].remove(connection)
                            self._connection_counts[device_key] -= 1

            # If no reusable connection, establish a new one
            print(f"Attempting to connect to {device_info.ip_address}...")
            try:
                # Perform a quick TCP port check
                if not self._check_tcp_port_open(device_info.ip_address, device_info.port):
                    # Update database and invalidate cache when device is unreachable
                    self._update_device_reachability(device_info, False)
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
                
                # Update database and invalidate cache when device is reachable
                is_reachable = self._update_device_reachability(device_info, True)
                if not is_reachable:
                    # If update failed, raise an exception
                    raise DeviceUnreachableError(f"Failed to update reachability for device {device_info.ip_address}")
                
                print(f"Successfully connected to {device_info.ip_address}.")
                return connection
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                print(f"Connection failed for {device_info.ip_address}: {e}")
                # Update database and invalidate cache when device is unreachable
                is_reachable = self._update_device_reachability(device_info, False)
                if is_reachable:
                    # If update failed, raise an exception
                    raise DeviceUnreachableError(f"Failed to update reachability for device {device_info.ip_address}")
                raise
            except DeviceUnreachableError:
                # Already updated in the TCP port check, just re-raise
                raise
            except Exception as e:
                print(f"An unexpected error occurred during connection to {device_info.ip_address}: {e}")
                # Update database and invalidate cache when device is unreachable
                is_reachable = self._update_device_reachability(device_info, False)
                if is_reachable:
                    # If update failed, raise an exception
                    raise DeviceUnreachableError(f"Failed to update reachability for device {device_info.ip_address}")
                raise

    def _validate_connection(self, connection) -> bool:
        """
        Validates if a connection is still alive and responsive.
        """
        try:
            # Check if the connection is alive using Netmiko's built-in method
            if not connection.is_alive():
                return False

            return True
        except Exception:
            # If any exception occurs during validation, consider the connection invalid
            return False

    def _execute_with_queue(self, device_info: DeviceConnectionInfo, operation_func, timeout: int = None):
        """
        Execute an operation with a per-device request queue to prevent blocking across devices.
        """
        device_key = device_info.get_key()
        
        # Create a future to return immediately
        future = Future()
        
        # Add the operation to the device's request queue
        request_item = {
            'operation_func': operation_func,
            'future': future,
            'timeout': timeout
        }
        
        # Ensure the queue exists for this device
        if device_key not in self._request_queues:
            self._request_queues[device_key] = queue.Queue()
        
        self._request_queues[device_key].put(request_item)
        
        # Process the queue in a separate thread to avoid blocking
        self._executor.submit(self._process_device_queue, device_key)
        
        return future

    def _process_device_queue(self, device_key: str):
        """
        Process the request queue for a specific device in bulk.
        """
        if device_key not in self._request_queues:
            return
            
        queue_for_device = self._request_queues[device_key]
        
        # Collect all items in the queue for bulk processing
        request_items = []
        while not queue_for_device.empty():
            try:
                request_item = queue_for_device.get_nowait()
                request_items.append(request_item)
            except queue.Empty:
                break
        
        # Execute all operations in parallel
        for request_item in request_items:
            future = request_item['future']
            operation_func = request_item['operation_func']
            timeout = request_item['timeout']
            
            # Execute the operation
            try:
                result = operation_func()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

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
        """Submits a connection request with per-device queuing and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
        def retry_connect_device():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return self._connect_device(device_info, netmiko_device_type)
                except (NetmikoTimeoutException, NetmikoAuthenticationException, DeviceUnreachableError) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Connection failed for {device_info.ip_address} after {max_retries} attempts: {e}")
                        raise e
                    # Exponential backoff: wait 1s, then 2s, then 4s
                    wait_time = 2 ** attempt
                    print(f"Connection failed for {device_info.ip_address}, attempt {attempt + 1}. Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    # For other exceptions, don't retry
                    print(f"Non-retryable error during connection to {device_info.ip_address}: {e}")
                    raise e
        
        return self._execute_with_queue(device_info, retry_connect_device)

    def send_command(self, device_info: DeviceConnectionInfo, command: str, netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a command execution request with per-device queuing and returns a Future."""
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

        def retry_execute_command():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return _execute_command()
                except (NetmikoTimeoutException, NetmikoAuthenticationException, DeviceUnreachableError) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Command execution failed for {device_info.ip_address} after {max_retries} attempts: {e}")
                        raise e
                    # Exponential backoff: wait 1s, then 2s, then 4s
                    wait_time = 2 ** attempt
                    print(f"Command execution failed for {device_info.ip_address}, attempt {attempt + 1}. Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    # For other exceptions, don't retry
                    print(f"Non-retryable error during command execution for {device_info.ip_address}: {e}")
                    raise e
        
        return self._execute_with_queue(device_info, retry_execute_command, timeout)

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a config set execution request with per-device queuing and returns a Future."""
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

        def retry_execute_config_set():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return _execute_config_set()
                except (NetmikoTimeoutException, NetmikoAuthenticationException, DeviceUnreachableError) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Config set execution failed for {device_info.ip_address} after {max_retries} attempts: {e}")
                        raise e
                    # Exponential backoff: wait 1s, then 2s, then 4s
                    wait_time = 2 ** attempt
                    print(f"Config set execution failed for {device_info.ip_address}, attempt {attempt + 1}. Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    # For other exceptions, don't retry
                    print(f"Non-retryable error during config set execution for {device_info.ip_address}: {e}")
                    raise e
        
        return self._execute_with_queue(device_info, retry_execute_config_set, timeout)

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a multiline command execution request with per-device queuing and returns a Future."""
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

        def retry_execute_multiline_commands():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return _execute_multiline_commands()
                except (NetmikoTimeoutException, NetmikoAuthenticationException, DeviceUnreachableError) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Multiline command execution failed for {device_info.ip_address} after {max_retries} attempts: {e}")
                        raise e
                    # Exponential backoff: wait 1s, then 2s, then 4s
                    wait_time = 2 ** attempt
                    print(f"Multiline command execution failed for {device_info.ip_address}, attempt {attempt + 1}. Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                except Exception as e:
                    # For other exceptions, don't retry
                    print(f"Non-retryable error during multiline command execution for {device_info.ip_address}: {e}")
                    raise e
        
        return self._execute_with_queue(device_info, retry_execute_multiline_commands, timeout)

    def _update_device_reachability(self, device_info: DeviceConnectionInfo, is_reachable: bool):
        """
        Update the device's reachability status in the database and invalidate cache.
        """
        if device_info.id is None:
            # If device ID is not available, we can't update the database
            return
            
        db = None
        try:
            db = SessionLocal()
            db_device = crud.get_device(db, device_id=device_info.id)
            
            if db_device and db_device.is_reachable != is_reachable:
                # Create a DeviceUpdate object to update the reachability status
                device_update = DeviceUpdate(is_reachable=is_reachable)
                crud.update_device(db, device_info.id, device_update)
                print(f"Updated reachability for device {device_info.id} to {is_reachable}")

                
                
                # Return the updated status directly from the database
                return crud.get_device(db, device_id=device_info.id).is_reachable
        except Exception as e:
            print(f"Failed to update reachability status for device {device_info.id}: {str(e)}")
        finally:
            if db:
                db.close()
                
        return is_reachable

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
            
            # Only shutdown if not already shutdown
            if not self._executor_shutdown:
                self._executor.shutdown(wait=True)
                self._executor_shutdown = True
            print("All connections disconnected and executor shut down.")
