import threading
import socket
import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict
from contextlib import closing
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from src.config import settings
from src.device_info import DeviceConnectionInfo
from src.exceptions import DeviceUnreachableError
from src.database import SessionLocal
from src.crud import crud
from src.schemas import DeviceUpdate

NETMIKO_DEVICE_TYPE_MAP = {
    "cisco_ios_router": "cisco_ios",
    "cisco_ios_switch": "cisco_ios",
    "aruba_procurve": "hp_procurve",
    "ubiquiti_unifiswitch": "ubiquiti_unifiswitch_ssh",
}

class ConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConnectionManager, cls).__new__(cls)
                    cls._instance._connection_pools = {}  # device_key -> list of connections
                    cls._instance._connection_locks = {}  # device_key -> lock for pool access
                    cls._instance._device_semaphores = {}  # device_key -> threading.Semaphore for max concurrent connections
                    cls._instance._request_queues = {}  # device_key -> queue.Queue for pending requests
                    cls._instance._pool_sizes = {}  # device_key -> max connections in pool
                    cls._instance._failed_operations = defaultdict(list)  # device_key -> list of (operation_func, future, retry_count)
                    cls._instance._max_operation_retries = 3
                    cls._instance._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER_THREADS)
                    cls._instance._executor_shutdown = False

                    # Connection health tracking
                    cls._instance._connection_last_success = {}  # device_key -> timestamp
                    cls._instance._connection_failures = {}  # device_key -> failure_count
                    cls._instance._max_consecutive_failures = 2

                    cls._instance._default_pool_size = 3  # Default max concurrent connections per device
        return cls._instance

    def _debug_log(self, message: str, device_key: str = ""):
        """Enhanced debugging with timestamps and device context"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if device_key:
            print(f"[{timestamp}] [{device_key}] {message}")
        else:
            print(f"[{timestamp}] {message}")

    def _check_tcp_port_open(self, ip_address: str, port: int, timeout: float = 2.0) -> bool:
        """Checks if a TCP port is open on a given IP address using socket.create_connection for reliable timeout."""

        self._debug_log(f"Checking TCP port {port} on {ip_address}")

        try:
            # socket.create_connection is more reliable for timeouts than raw socket.connect
            with closing(socket.create_connection((ip_address, port), timeout=timeout)) as sock:
                self._debug_log(f"TCP port {port} on {ip_address} is OPEN")
                return True
        except socket.timeout:
            self._debug_log(f"TCP port {port} on {ip_address} is CLOSED: connection timed out")
            return False
        except ConnectionRefusedError:
            self._debug_log(f"TCP port {port} on {ip_address} is CLOSED: connection refused")
            return False
        except OSError as e:
            self._debug_log(f"TCP port {port} on {ip_address} is CLOSED: OS error - {e}")
            return False
        except Exception as e:
            self._debug_log(f"TCP port {port} on {ip_address} is CLOSED: unexpected error - {e}")
            return False

    def _validate_connection_responsive(self, connection, device_info: DeviceConnectionInfo) -> bool:
        """Improved validation that tests if connection is responsive."""
        device_key = device_info.get_key()
        self._debug_log("Starting connection responsiveness test", device_key)
        try:
            # Clear buffer more aggressively
            for _ in range(3):
                connection.clear_buffer()
                time.sleep(0.1)
            
            self._debug_log("Buffer cleared, sending test command", device_key)
            
            # Use a more reliable test command with explicit pattern matching
            test_output = connection.send_command(
                "\n",
                expect_string=r'[>#]',
                read_timeout=15,  # Increased timeout
                strip_prompt=False,
                strip_command=False,
                delay_factor=2.0  # Add delay factor for slow devices
            )
            
            # More robust check for responsiveness
            is_responsive = bool(test_output and any(char in test_output for char in ['>', '#']))
            self._debug_log(f"Connection responsiveness test result: {is_responsive}", device_key)
            return is_responsive
            
        except Exception as e:
            self._debug_log(f"Connection responsiveness test FAILED: {e}", device_key)
            self._debug_log(f"Full traceback: {traceback.format_exc()}", device_key)
            return False

    def _mark_connection_failure(self, device_key: str):
        """Track consecutive failures for a device."""
        if device_key not in self._connection_failures:
            self._connection_failures[device_key] = 0
        self._connection_failures[device_key] += 1
        self._debug_log(f"Connection failure #{self._connection_failures[device_key]}", device_key)

    def _mark_connection_success(self, device_key: str):
        """Reset failure counter on successful command."""
        if device_key in self._connection_failures:
            self._connection_failures[device_key] = 0
        self._connection_last_success[device_key] = time.time()
        self._debug_log("Connection marked as successful", device_key)

    def _should_drop_connection(self, device_key: str) -> bool:
        """Determine if connection should be dropped due to repeated failures."""
        if (device_key in self._connection_failures and 
            self._connection_failures[device_key] >= self._max_consecutive_failures):
            self._debug_log(f"Dropping connection due to {self._max_consecutive_failures} consecutive failures", device_key)
            return True
        return False

    def _cleanup_stale_connection(self, device_key: str):
        """Clean up stale connections in the pool."""
        if device_key in self._connection_pools:
            with self._connection_locks[device_key]:
                pool = self._connection_pools[device_key]
                for i, conn_info in enumerate(pool[:]):  # Use slice to avoid modification during iteration
                    connection = conn_info['connection']
                    try:
                        if connection.is_alive():
                            connection.disconnect()
                        self._debug_log("Cleaned up stale connection", device_key)
                    except Exception as e:
                        self._debug_log(f"Error during stale connection cleanup: {e}", device_key)
                    finally:
                        # Remove from pool
                        if i < len(pool):
                            pool.pop(i)

    def quick_check_reachability(self, device_info: DeviceConnectionInfo) -> bool:
        """
        Fast reachability check using only TCP port check without acquiring connection pool resources.
        This is designed for the periodic reachability task that runs every 5 seconds.
        """
        try:
            # Perform a simple TCP port check without acquiring locks or connections
            is_reachable = self._check_tcp_port_open(device_info.ip_address, device_info.port, timeout=2.0)
            device_key = device_info.get_key()

            if is_reachable:
                self._debug_log("TCP port is open", device_key)
                self._mark_connection_success(device_key)  # Consider successful TCP as success for reachability
            else:
                self._debug_log("TCP port is closed", device_key)
                self._mark_connection_failure(device_key)  # Mark as failure for reachability

            return is_reachable
        except Exception as e:
            device_key = device_info.get_key()
            self._debug_log(f"Error during quick reachability check: {e}", device_key)
            self._mark_connection_failure(device_key)
            return False

    def _is_netmiko_error_retryable(self, error: Exception) -> bool:
        """Check if a Netmiko error is retryable (pattern detection errors, timeouts, etc.)"""
        error_str = str(error).lower()
        traceback_str = traceback.format_exc().lower()
        
        self._debug_log(f"Checking if error is retryable: {error_str}")
        
        # Connection-related errors (retryable)
        retryable_errors = [
            "pattern not detected",
            "failed to send command",
            "connection closed", 
            "session disconnected", 
            "socket is closed",
            "timed out",
            "timeout",
            "read timeout",
            "connection reset",
            "broken pipe",
        ]
        
        for term in retryable_errors:
            if term in error_str or term in traceback_str:
                self._debug_log(f"Error is RETRYABLE: {term}")
                return True
        
        self._debug_log("Error is NOT retryable")
        return False

    def _get_connection_from_pool(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Get an available connection from the pool, or create a new one if needed."""
        device_key = device_info.get_key()

        # Initialize device-specific resources if not already done
        if device_key not in self._connection_locks:
            with self._lock:  # Use class lock to avoid race conditions during init
                if device_key not in self._connection_locks:
                    self._connection_locks[device_key] = threading.RLock()  # Reentrant lock
                    self._connection_pools[device_key] = []
                    # Set semaphore to control max concurrent connections per device
                    pool_size = self._pool_sizes.get(device_key, self._default_pool_size)
                    self._device_semaphores[device_key] = threading.Semaphore(pool_size)
                    self._request_queues[device_key] = queue.Queue()

        # Acquire a slot for the connection (blocking if too many concurrent connections)
        if not self._device_semaphores[device_key].acquire(blocking=True, timeout=settings.NETMIKO_TIMEOUT):
            raise DeviceUnreachableError(f"Unable to acquire connection slot for {device_key}")

        with self._connection_locks[device_key]:
            # Look for an available connection in the pool
            for i, connection_info in enumerate(self._connection_pools[device_key]):
                connection = connection_info['connection']
                if connection_info['available'] and connection.is_alive():
                    if self._validate_connection_responsive(connection, device_info):
                        # Mark this connection as unavailable
                        connection_info['available'] = False
                        self._debug_log("Reusing connection from pool", device_key)
                        return connection, i  # Return the connection and its index in the pool

            # No available connection found, create a new one
            self._debug_log("Creating new connection", device_key)
            connection = self._create_new_connection(device_info, netmiko_device_type)

            # Add new connection to pool
            connection_info = {
                'connection': connection,
                'available': False,
                'last_used': time.time()
            }
            self._connection_pools[device_key].append(connection_info)

            return connection, len(self._connection_pools[device_key]) - 1

    def _return_connection_to_pool(self, device_info: DeviceConnectionInfo, connection_index: int):
        """Return a connection to the pool after use."""
        device_key = device_info.get_key()

        if device_key in self._connection_locks:
            with self._connection_locks[device_key]:
                if (device_key in self._connection_pools and
                    connection_index < len(self._connection_pools[device_key])):
                    connection_info = self._connection_pools[device_key][connection_index]
                    connection_info['available'] = True
                    connection_info['last_used'] = time.time()

        # Release the semaphore to allow new connections
        if device_key in self._device_semaphores:
            self._device_semaphores[device_key].release()

    def _create_new_connection(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Creates a new Netmiko connection to the device."""
        device_key = device_info.get_key()

        # Check if the port is open first
        if not self._check_tcp_port_open(device_info.ip_address, device_info.port):
            self._update_device_reachability(device_info, False)
            raise DeviceUnreachableError(f"TCP connection to device {device_info.ip_address}:{device_info.port} failed.")

        netmiko_type = NETMIKO_DEVICE_TYPE_MAP.get(device_info.device_type, device_info.device_type)
        self._debug_log(f"Creating Netmiko connection with type: {netmiko_type}", device_key)

        # Enhanced connection parameters for better stability
        connection_params = {
            'device_type': netmiko_type,
            'host': device_info.ip_address,
            'username': device_info.username,
            'password': device_info.password,
            'secret': device_info.secret,
            'port': device_info.port,
            'timeout': settings.NETMIKO_TIMEOUT,
            'session_timeout': settings.NETMIKO_TIMEOUT + 10,
            'global_delay_factor': 2.0,  # Increased for stability
            'fast_cli': False,
        }

        # Add optional parameters if they exist in settings
        if hasattr(settings, 'NETMIKO_BANNER_TIMEOUT'):
            connection_params['banner_timeout'] = settings.NETMIKO_BANNER_TIMEOUT
        if hasattr(settings, 'NETMIKO_SESSION_LOG'):
            connection_params['session_log'] = settings.NETMIKO_SESSION_LOG

        connection = ConnectHandler(**connection_params)

        if not self._validate_connection_responsive(connection, device_info):
            self._debug_log("New connection is unresponsive, dropping", device_key)
            connection.disconnect()
            raise DeviceUnreachableError(f"New connection to {device_info.ip_address} is unresponsive")

        self._mark_connection_success(device_key)
        is_reachable = self._update_device_reachability(device_info, True)
        if not is_reachable:
            raise DeviceUnreachableError(f"Failed to update reachability for device {device_info.ip_address}")

        self._debug_log("Successfully connected", device_key)
        return connection

    def _retry_failed_operations(self, device_key: str):
        """Retry any failed operations for this device when getting a fresh connection"""
        if device_key in self._failed_operations:
            self._debug_log(f"Clearing {len(self._failed_operations[device_key])} failed operations for {device_key}", device_key)
            self._failed_operations[device_key].clear()

    def _execute_operation_with_connection(self, future: Future, operation_func, device_info: DeviceConnectionInfo, timeout: int = None, current_retry: int = 0):
        """
        Execute a single operation with connection from the pool and automatic retry on Netmiko errors.
        """
        device_key = device_info.get_key()

        if future.done():
            self._debug_log("Future already done, skipping", device_key)
            return

        connection = None
        connection_index = None

        try:
            self._debug_log(f"Acquiring connection from pool and executing operation (retry #{current_retry})", device_key)

            # Get a connection from the pool
            connection, connection_index = self._get_connection_from_pool(device_info,
                                                                         NETMIKO_DEVICE_TYPE_MAP.get(device_info.device_type, device_info.device_type))

            # Execute the operation function with the acquired connection
            result = operation_func(connection)

            if not future.done():
                future.set_result(result)
                self._debug_log("Operation completed successfully", device_key)
                self._mark_connection_success(device_key)

        except Exception as e:
            self._debug_log(f"Operation failed (retry #{current_retry}): {e}", device_key)
            self._debug_log(f"Full error: {traceback.format_exc()}", device_key)

            # Check if this error is retryable
            is_retryable = self._is_netmiko_error_retryable(e)

            if current_retry < self._max_operation_retries and is_retryable:
                self._debug_log(f"Error is retryable, scheduling retry #{current_retry + 1}", device_key)

                # Wait before the next connection attempt (exponential backoff)
                wait_time = min(2 ** current_retry, 10)
                self._debug_log(f"Waiting {wait_time}s before retry", device_key)
                time.sleep(wait_time)

                # Retry the operation directly by calling it again
                self._execute_operation_with_connection(future, operation_func, device_info, timeout, current_retry + 1)
                return

            else:
                # Not retryable or max retries exceeded
                if not is_retryable:
                    self._debug_log("Error is NOT retryable, failing operation", device_key)
                else:
                    self._debug_log(f"Max retries ({self._max_operation_retries}) exceeded, failing operation", device_key)

                self._mark_connection_failure(device_key)
                if not future.done():
                    future.set_exception(e)
        finally:
            if connection is not None and connection_index is not None:
                self._return_connection_to_pool(device_info, connection_index)

    def get_connection(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Submits a connection request and returns a Future that resolves to the connection."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")

        future = Future()

        def operation_func(connection):
            # Return the connection object directly
            return connection

        self._execute_operation_with_connection(future, operation_func, device_info)
        return future

    def send_command(self, device_info: DeviceConnectionInfo, command: str, netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a command execution request and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")

        future = Future()

        def operation_func(connection):
            device_key = device_info.get_key()
            try:
                if not connection.check_enable_mode():
                    connection.enable()

                # Clear buffer multiple times to ensure clean state
                for _ in range(3):
                    connection.clear_buffer()
                    time.sleep(0.05)

                self._debug_log(f"Executing command: {command}", device_key)
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT

                # Enhanced command execution with better error handling
                output = connection.send_command(
                    command,
                    read_timeout=cmd_timeout,
                    expect_string=None,
                    delay_factor=2.0,  # Added for stability
                    max_loops=1000,    # Increased for long outputs
                    **kwargs
                )
                self._debug_log(f"Command executed successfully: {command}", device_key)
                return output

            except Exception as e:
                self._debug_log(f"Error executing command '{command}': {e}", device_key)
                raise

        self._execute_operation_with_connection(future, operation_func, device_info, timeout)
        return future

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a config set execution request and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")

        future = Future()

        def operation_func(connection):
            device_key = device_info.get_key()
            try:
                if not connection.check_enable_mode():
                    connection.enable()

                self._debug_log(f"Executing {len(commands)} config commands", device_key)
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_config_set(
                    commands,
                    read_timeout=cmd_timeout,  # Use read_timeout instead of cmd_timeout
                    delay_factor=2.0,  # Added for stability
                    **kwargs
                )
                self._debug_log("Config commands executed successfully", device_key)
                return output

            except Exception as e:
                self._debug_log(f"Error executing config commands: {e}", device_key)
                raise

        self._execute_operation_with_connection(future, operation_func, device_info, timeout)
        return future

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a multiline command execution request and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")

        future = Future()

        def operation_func(connection):
            device_key = device_info.get_key()
            try:
                if not connection.check_enable_mode():
                    connection.enable()

                self._debug_log(f"Executing {len(command_patterns)} multiline commands", device_key)
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_multiline(
                    command_patterns,
                    read_timeout=cmd_timeout,
                    delay_factor=2.0,  # Added for stability
                    **kwargs
                )
                self._debug_log("Multiline commands executed successfully", device_key)
                return output

            except Exception as e:
                self._debug_log(f"Error executing multiline commands: {e}", device_key)
                raise

        self._execute_operation_with_connection(future, operation_func, device_info, timeout)
        return future

    def _update_device_reachability(self, device_info: DeviceConnectionInfo, is_reachable: bool):
        """Update device reachability status."""
        if device_info.id is None:            
            return
            
        db = None
        try:
            db = SessionLocal()
            db_device = crud.get_device(db, device_id=device_info.id)
            
            if db_device and db_device.is_reachable != is_reachable:
                device_update = DeviceUpdate(is_reachable=is_reachable)
                crud.update_device(db, device_info.id, device_update)
                self._debug_log(f"Updated reachability to {is_reachable}", device_info.get_key())
                return crud.get_device(db, device_id=device_info.id).is_reachable
        except Exception as e:
            self._debug_log(f"Failed to update reachability: {e}", device_info.get_key())
        finally:
            if db:
                db.close()
        return is_reachable

    def disconnect_all(self):
        """Disconnects all active Netmiko connections."""
        with self._lock:
            # Fail all pending operations
            for device_key in list(self._failed_operations.keys()):
                for _, future, _ in self._failed_operations[device_key]:
                    if not future.done():
                        future.set_exception(Exception("Connection manager shutdown"))
                self._failed_operations[device_key].clear()

            # Disconnect all connections in all pools
            for device_key, pool in list(self._connection_pools.items()):
                for connection_info in pool:
                    connection = connection_info['connection']
                    if connection:
                        try:
                            connection.disconnect()
                            self._debug_log("Disconnected", device_key)
                        except Exception as e:
                            self._debug_log(f"Error disconnecting: {e}", device_key)

            # Clear all pools
            self._connection_pools.clear()

            # Clear all tracking
            self._connection_failures.clear()
            self._connection_last_success.clear()
            self._failed_operations.clear()

            # Shutdown executor
            if not self._executor_shutdown:
                self._executor.shutdown(wait=True)
                self._executor_shutdown = True
            self._debug_log("All connections disconnected and executor shut down")