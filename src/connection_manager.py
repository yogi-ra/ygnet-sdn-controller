import threading
import socket
import queue
import time
import traceback
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
}

class ConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConnectionManager, cls).__new__(cls)
                    # SIMPLIFIED: Only one connection per device
                    cls._instance._connections = {}  # device_key -> connection object (SINGLE connection)
                    cls._instance._connection_locks = {}  # device_key -> lock
                    cls._instance._connection_conditions = {}  # device_key -> threading.Condition
                    cls._instance._request_queues = {}  # device_key -> queue.Queue for pending requests
                    
                    # NEW: Track if a device is currently processing
                    cls._instance._device_busy = {}  # device_key -> bool
                    cls._instance._queue_processing = {}  # device_key -> bool (track if queue is being processed)
                    
                    # NEW: Failed operations tracking for automatic retry
                    cls._instance._failed_operations = defaultdict(list)  # device_key -> list of (operation_func, future, retry_count)
                    cls._instance._max_operation_retries = 3
                    
                    cls._instance._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKER_THREADS)
                    cls._instance._executor_shutdown = False
                    
                    # Connection health tracking
                    cls._instance._connection_last_success = {}  # device_key -> timestamp
                    cls._instance._connection_failures = {}  # device_key -> failure_count
                    cls._instance._max_consecutive_failures = 2
        return cls._instance

    def _debug_log(self, message: str, device_key: str = ""):
        """Enhanced debugging with timestamps and device context"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if device_key:
            print(f"[{timestamp}] [{device_key}] {message}")
        else:
            print(f"[{timestamp}] {message}")

    def _check_tcp_port_open(self, ip_address: str, port: int, timeout: float = 2.0) -> bool:
        """Checks if a TCP port is open on a given IP address."""
        self._debug_log(f"Checking TCP port {port} on {ip_address}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip_address, port))
            self._debug_log(f"TCP port {port} on {ip_address} is OPEN")
            return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._debug_log(f"TCP port {port} on {ip_address} is CLOSED: {e}")
            return False
        finally:
            sock.close()

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
        """Clean up a stale connection completely."""
        if device_key in self._connections and self._connections[device_key]:
            connection = self._connections[device_key]
            try:
                if connection.is_alive():
                    connection.disconnect()
                self._debug_log("Cleaned up stale connection", device_key)
            except Exception as e:
                self._debug_log(f"Error during stale connection cleanup: {e}", device_key)
            finally:
                self._connections[device_key] = None

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

    def _connect_device(self, device_info: DeviceConnectionInfo, netmiko_device_type: str):
        """Establishes a Netmiko connection to the device - SERIALIZED per device."""
        device_key = device_info.get_key()
        self._debug_log("Starting connection process", device_key)
        
        # Initialize synchronization primitives for this device
        if device_key not in self._connection_locks:
            self._connection_locks[device_key] = threading.Lock()
        if device_key not in self._connection_conditions:
            self._connection_conditions[device_key] = threading.Condition(self._connection_locks[device_key])
        if device_key not in self._request_queues:
            self._request_queues[device_key] = queue.Queue()
        if device_key not in self._device_busy:
            self._device_busy[device_key] = False

        with self._connection_conditions[device_key]:
            # Wait if device is currently busy
            while self._device_busy[device_key]:
                self._debug_log("Device is busy, waiting...", device_key)
                self._connection_conditions[device_key].wait()

            # Mark device as busy
            self._device_busy[device_key] = True
            self._debug_log("Device marked as busy", device_key)

            try:
                # Check if we have an existing connection that might be reusable
                if (device_key in self._connections and 
                    self._connections[device_key] is not None and
                    not self._should_drop_connection(device_key)):
                    
                    connection = self._connections[device_key]
                    try:
                        # Perform TCP port check first
                        if not self._check_tcp_port_open(device_info.ip_address, device_info.port):
                            self._debug_log("Device port is closed, removing connection", device_key)
                            self._cleanup_stale_connection(device_key)
                            self._update_device_reachability(device_info, False)
                        else:
                            # Test connection responsiveness
                            if (connection.is_alive() and 
                                self._validate_connection_responsive(connection, device_info)):
                                self._debug_log("Reusing responsive connection", device_key)
                                return connection
                            else:
                                self._debug_log("Unresponsive connection found, removing", device_key)
                                self._cleanup_stale_connection(device_key)
                    except Exception as e:
                        self._debug_log(f"Error checking connection: {e}, removing", device_key)
                        self._cleanup_stale_connection(device_key)

                # If no reusable connection, establish a new one
                self._debug_log("Attempting fresh connection", device_key)
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
                
                # Store the single connection for this device
                self._connections[device_key] = connection
                self._mark_connection_success(device_key)
                
                is_reachable = self._update_device_reachability(device_info, True)
                if not is_reachable:
                    raise DeviceUnreachableError(f"Failed to update reachability for device {device_info.ip_address}")
                
                self._debug_log("Successfully connected", device_key)
                
                # NEW: Retry any failed operations when we establish a fresh connection
                self._retry_failed_operations(device_key)
                
                return connection
                
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
                self._debug_log(f"Connection failed: {e}", device_key)
                self._update_device_reachability(device_info, False)
                self._mark_connection_failure(device_key)
                raise
            except DeviceUnreachableError:
                self._mark_connection_failure(device_key)
                raise
            except Exception as e:
                self._debug_log(f"Unexpected error during connection: {e}", device_key)
                self._debug_log(f"Full traceback: {traceback.format_exc()}", device_key)
                self._update_device_reachability(device_info, False)
                self._mark_connection_failure(device_key)
                raise

    def _retry_failed_operations(self, device_key: str):
        """Retry any failed operations for this device when we get a fresh connection"""
        if device_key in self._failed_operations and self._failed_operations[device_key]:
            self._debug_log(f"Retrying {len(self._failed_operations[device_key])} failed operations", device_key)
            
            # Get a copy to avoid modification during iteration
            failed_ops = self._failed_operations[device_key][:]
            self._failed_operations[device_key].clear()
            
            for operation_func, future, retry_count in failed_ops:
                try:
                    # Resubmit the operation with incremented retry count
                    if device_key not in self._request_queues:
                        self._request_queues[device_key] = queue.Queue()
                    
                    self._request_queues[device_key].put({
                        'operation_func': operation_func,
                        'future': future,
                        'timeout': None,
                        'device_info': getattr(future, '_device_info', None),
                        'retry_count': retry_count + 1
                    })
                    self._debug_log(f"Resubmitted failed operation (retry #{retry_count + 1})", device_key)
                    
                    # Ensure queue processing is running
                    self._ensure_queue_processing(device_key)
                    
                except Exception as e:
                    self._debug_log(f"Error resubmitting failed operation: {e}", device_key)
                    if not future.done():
                        future.set_exception(e)

    def _release_connection(self, device_info: DeviceConnectionInfo):
        """Release a device - mark it as available for the next operation."""
        device_key = device_info.get_key()
        with self._connection_conditions[device_key]:
            # Mark device as available
            self._device_busy[device_key] = False
            # Notify waiting threads that the device is available
            self._connection_conditions[device_key].notify_all()
            self._debug_log("Device released and available", device_key)

    def _ensure_queue_processing(self, device_key: str):
        """Ensure that queue processing is running for a device."""
        if not hasattr(self, '_queue_processing'):
            self._queue_processing = {}
            
        if device_key not in self._queue_processing or not self._queue_processing[device_key]:
            self._queue_processing[device_key] = True
            self._executor.submit(self._process_device_queue, device_key)

    def _execute_with_queue(self, device_info: DeviceConnectionInfo, operation_func, timeout: int = None):
        """
        Execute an operation with strict serialization per device.
        """
        device_key = device_info.get_key()
        self._debug_log("Submitting operation to queue", device_key)
        
        future = Future()
        
        request_item = {
            'operation_func': operation_func,
            'future': future,
            'timeout': timeout,
            'device_info': device_info,
            'retry_count': 0  # Initial request
        }
        
        # Ensure queue exists for this device
        if device_key not in self._request_queues:
            self._request_queues[device_key] = queue.Queue()
        
        # Add to device-specific queue
        self._request_queues[device_key].put(request_item)
        
        # Start queue processing if not already running
        self._ensure_queue_processing(device_key)
        
        self._debug_log(f"Operation queued (queue size: {self._request_queues[device_key].qsize()})", device_key)
        return future

    def _process_device_queue(self, device_key: str):
        """
        Process the request queue for a specific device - SERIALLY, one at a time.
        This is the KEY FIX: Process operations sequentially in THIS thread, not by submitting to executor.
        """
        self._debug_log("Starting queue processing", device_key)
        
        if device_key not in self._request_queues:
            self._queue_processing[device_key] = False
            return
            
        queue_for_device = self._request_queues[device_key]
        
        # Process requests ONE AT A TIME for this device IN THIS THREAD
        while True:
            try:
                # Use get with timeout to allow clean shutdown
                request_item = queue_for_device.get(timeout=1.0)
                future = request_item['future']
                operation_func = request_item['operation_func']
                timeout = request_item['timeout']
                device_info = request_item['device_info']
                retry_count = request_item.get('retry_count', 0)
                
                # Store device info on future for retry purposes
                future._device_info = device_info
                future._retry_count = retry_count
                
                self._debug_log(f"Processing operation (retry #{retry_count})", device_key)
                
                # EXECUTE IN CURRENT THREAD - This ensures true serialization
                self._execute_single_operation_with_retry(future, operation_func, device_info, timeout, retry_count)
                
                self._debug_log(f"Operation completed (queue size: {queue_for_device.qsize()})", device_key)
                
            except queue.Empty:
                # No more items in queue, exit processing
                break
            except Exception as e:
                self._debug_log(f"Unexpected error in queue processing: {e}", device_key)
                # Continue processing other items despite errors
        
        # Mark that we're no longer processing this device's queue
        self._queue_processing[device_key] = False
        self._debug_log("Queue processing completed", device_key)

    def _execute_single_operation_with_retry(self, future: Future, operation_func, device_info: DeviceConnectionInfo, timeout: int = None, current_retry: int = 0):
        """
        Execute a single operation with automatic retry on Netmiko errors.
        """
        device_key = device_info.get_key()
        
        if future.done():
            self._debug_log("Future already done, skipping", device_key)
            return
            
        try:
            self._debug_log(f"Executing operation (retry #{current_retry})", device_key)
            
            # This will acquire the device lock and wait if device is busy
            result = operation_func()
            if not future.done():
                future.set_result(result)
                self._debug_log("Operation completed successfully", device_key)
                
        except Exception as e:
            self._debug_log(f"Operation failed (retry #{current_retry}): {e}", device_key)
            self._debug_log(f"Full error: {traceback.format_exc()}", device_key)
            
            # Check if this error is retryable
            is_retryable = self._is_netmiko_error_retryable(e)
            
            if current_retry < self._max_operation_retries and is_retryable:
                self._debug_log(f"Error is retryable, scheduling retry #{current_retry + 1}", device_key)
                
                # Clean up the connection on failure
                self._cleanup_stale_connection(device_key)
                
                # Store for retry
                if device_key not in self._failed_operations:
                    self._failed_operations[device_key] = []
                
                self._failed_operations[device_key].append((operation_func, future, current_retry))
                
                # Wait before the next connection attempt (exponential backoff)
                wait_time = min(2 ** current_retry, 10)
                self._debug_log(f"Waiting {wait_time}s before retry", device_key)
                time.sleep(wait_time)
                
            else:
                # Not retryable or max retries exceeded
                if not is_retryable:
                    self._debug_log("Error is NOT retryable, failing operation", device_key)
                else:
                    self._debug_log(f"Max retries ({self._max_operation_retries}) exceeded, failing operation", device_key)
                    
                if not future.done():
                    future.set_exception(e)
        finally:
            # Always release the device
            self._release_connection(device_info)

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
                    if attempt == max_retries - 1:
                        self._debug_log(f"Connection failed after {max_retries} attempts: {e}", device_info.get_key())
                        raise e
                    wait_time = 2 ** attempt
                    self._debug_log(f"Connection failed, attempt {attempt + 1}, retrying in {wait_time}s: {e}", device_info.get_key())
                    time.sleep(wait_time)
                except Exception as e:
                    self._debug_log(f"Non-retryable error during connection: {e}", device_info.get_key())
                    raise e
        
        return self._execute_with_queue(device_info, retry_connect_device)

    def send_command(self, device_info: DeviceConnectionInfo, command: str, netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a command execution request with per-device queuing and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_command():
            connection = None
            device_key = device_info.get_key()
            try:
                connection = self._connect_device(device_info, netmiko_device_type)
                
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
                self._mark_connection_success(device_key)
                self._debug_log(f"Command executed successfully: {command}", device_key)
                return output
                
            except Exception as e:
                self._debug_log(f"Error executing command '{command}': {e}", device_key)
                self._mark_connection_failure(device_key)
                raise
        
        return self._execute_with_queue(device_info, _execute_command, timeout)

    def send_config_set(self, device_info: DeviceConnectionInfo, commands: list[str], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a config set execution request with per-device queuing and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_config_set():
            connection = None
            device_key = device_info.get_key()
            try:
                connection = self._connect_device(device_info, netmiko_device_type)
                
                if not connection.check_enable_mode():
                    connection.enable()
                
                self._debug_log(f"Executing {len(commands)} config commands", device_key)
                cmd_timeout = timeout or settings.NETMIKO_READ_TIMEOUT
                output = connection.send_config_set(
                    commands, 
                    cmd_timeout=cmd_timeout, 
                    delay_factor=2.0,  # Added for stability
                    **kwargs
                )
                self._mark_connection_success(device_key)
                self._debug_log("Config commands executed successfully", device_key)
                return output
                
            except Exception as e:
                self._debug_log(f"Error executing config commands: {e}", device_key)
                self._mark_connection_failure(device_key)
                raise

        return self._execute_with_queue(device_info, _execute_config_set, timeout)

    def send_multiline_commands(self, device_info: DeviceConnectionInfo, command_patterns: list[list[str]], netmiko_device_type: str, timeout: int = None, **kwargs):
        """Submits a multiline command execution request with per-device queuing and returns a Future."""
        if self._executor_shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown")
            
        def _execute_multiline_commands():
            connection = None
            device_key = device_info.get_key()
            try:
                connection = self._connect_device(device_info, netmiko_device_type)
                
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
                self._mark_connection_success(device_key)
                self._debug_log("Multiline commands executed successfully", device_key)
                return output
                
            except Exception as e:
                self._debug_log(f"Error executing multiline commands: {e}", device_key)
                self._mark_connection_failure(device_key)
                raise

        return self._execute_with_queue(device_info, _execute_multiline_commands, timeout)

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
            # Mark all queues as not processing
            if hasattr(self, '_queue_processing'):
                for device_key in list(self._queue_processing.keys()):
                    self._queue_processing[device_key] = False
            
            # Fail all pending operations
            for device_key in list(self._failed_operations.keys()):
                for _, future, _ in self._failed_operations[device_key]:
                    if not future.done():
                        future.set_exception(Exception("Connection manager shutdown"))
                self._failed_operations[device_key].clear()
            
            # Disconnect all connections
            for device_key, connection in list(self._connections.items()):
                if connection:
                    try:
                        connection.disconnect()
                        self._debug_log("Disconnected", device_key)
                    except Exception as e:
                        self._debug_log(f"Error disconnecting: {e}", device_key)
                self._connections[device_key] = None
            
            # Clear all tracking
            self._connection_failures.clear()
            self._connection_last_success.clear()
            self._failed_operations.clear()
            
            # Shutdown executor
            if not self._executor_shutdown:
                self._executor.shutdown(wait=True)
                self._executor_shutdown = True
            self._debug_log("All connections disconnected and executor shut down")