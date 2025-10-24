import asyncio
import socket
from sqlalchemy.orm import Session
from redis import Redis
import json

from src.celery_app import celery_app
from src.schemas import DeviceUpdate
from src.crud import crud
from src.database import SessionLocal
from src.config import settings

from src.api.utils import get_handler_from_device_id
from src.exceptions import DeviceConnectionError, DeviceUnreachableError, DeviceTimeoutError, DeviceAuthenticationError



@celery_app.task(bind=True)
def execute_netmiko_command_task(self, device_id: int, command: str, *args, **kwargs):
    """
    Celery task to execute a Netmiko command on a device asynchronously.

    Args:
        device_id (int): The ID of the device to connect to.
        command (str): The command to execute, in the format 'feature.method'.
        *args: Positional arguments to pass to the method.
        **kwargs: Keyword arguments to pass to the method.

    Returns:
        The result of the command execution.
    """
    db: Session = None
    try:
        db = SessionLocal()
        handler = get_handler_from_device_id(device_id, db)

        # The command is expected to be in 'feature.method' format
        # e.g., 'system.get_version_info' or 'interfaces.toggle_interface_state'
        feature_name, method_name = command.split('.')
        
        with handler:
            feature_handler = getattr(handler, feature_name)
            method_to_call = getattr(feature_handler, method_name)
            
            # Execute the method with provided arguments
            result = method_to_call(*args, **kwargs)
            return result
            
    except Exception as e:
        # Handle exceptions and update task state
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e  # Re-raise the exception to be caught by Celery worker
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def backup_devices_task(self, device_ids: list):
    """
    Celery task to backup configurations for multiple devices to FTP server.

    Args:
        device_ids (list): List of device IDs to backup

    Returns:
        dict: Backup results with success/failure status for each device
    """
    import asyncio
    import ftplib
    from datetime import datetime
    from io import BytesIO
    from concurrent.futures import ThreadPoolExecutor
    from src.config import settings
    from src.crud import crud
    from src.api.utils import get_handler_from_device_id
    
    db: Session = None
    try:
        db = SessionLocal()
        
        # Get device information from database
        devices = []
        for device_id in device_ids:
            db_device = crud.get_device(db, device_id=device_id)
            if not db_device:
                raise ValueError(f"Device with ID {device_id} not found")
            devices.append(db_device)
        
        # Get FTP configuration from settings
        ftp_config = {
            'host': settings.FTP_HOST,
            'username': settings.FTP_USERNAME,
            'password': settings.FTP_PASSWORD,
            'port': settings.FTP_PORT if hasattr(settings, 'FTP_PORT') else 21,
            'dest_dir': settings.FTP_DEST_DIR if hasattr(settings, 'FTP_DEST_DIR') else '/'
        }
        
        # Validate FTP configuration exists
        if not all([ftp_config['host'], ftp_config['username'], ftp_config['password']]):
            raise ValueError("FTP configuration not properly set in environment variables")
        
        # Define helper functions
        def connect_and_backup_device(device_info, db_session):
            """
            Connect to a device and backup its running configuration.

            Args:
                device_info (dict): Dictionary containing device information
                db_session: Database session

            Returns:
                str: Running configuration if successful, None otherwise
            """
            try:
                device_id = device_info.get('id')
                handler = get_handler_from_device_id(device_id, db_session)

                with handler:
                    # Get the running configuration
                    config = handler.system.get_running_config()
                    return config
            except Exception as e:
                print(f"Error backing up device {device_info.get('name', 'Unknown')}: {str(e)}")
                return None

        def upload_to_ftp(ftp_config, device_name, filename, file_content):
            """
            Upload a file to FTP server, creating a device-specific directory if needed.

            Args:
                ftp_config (dict): FTP server configuration
                device_name (str): Name of the device (used for directory creation)
                filename (str): Name of the file to upload
                file_content (str): Content of the file to upload

            Returns:
                bool: True if upload successful, False otherwise
            """
            try:
                # Connect to FTP server
                ftp = ftplib.FTP()
                ftp.connect(ftp_config['host'], ftp_config.get('port', 21))
                ftp.login(ftp_config['username'], ftp_config['password'])

                # Change to destination directory if specified
                if 'dest_dir' in ftp_config:
                    try:
                        ftp.cwd(ftp_config['dest_dir'])
                    except:
                        ftp.mkd(ftp_config['dest_dir'])
                        ftp.cwd(ftp_config['dest_dir'])

                # Create device-specific directory if it doesn't exist
                try:
                    ftp.cwd(device_name)
                except ftplib.error_perm:
                    # Directory doesn't exist, create it
                    print(f"Creating directory {device_name} on FTP server")
                    ftp.mkd(device_name)
                    ftp.cwd(device_name)

                file_data = BytesIO(file_content.encode())
                ftp.storbinary(f'STOR {filename}', file_data)

                # Close FTP connection
                ftp.quit()

                print(f"Successfully uploaded {filename} to FTP server in directory {device_name}")
                return True
            except Exception as e:
                print(f"Failed to upload {filename} to FTP server: {str(e)}")
                return False

        async def async_connect_and_backup_device(device_info, device_name, ftp_config, db_session):
            """
            Async wrapper for connecting and backing up a device, including FTP upload.

            Args:
                device_info (dict): Dictionary containing device information
                device_name (str): Name of the device
                ftp_config (dict): FTP configuration

            Returns:
                tuple: (device_name, success_status, error_message)
            """
            max_retries = 5
            retry_count = 0

            while retry_count < max_retries:
                try:
                    loop = asyncio.get_event_loop()

                    # Run the blocking backup operation in a thread pool
                    with ThreadPoolExecutor() as executor:
                        config_content = await loop.run_in_executor(executor, connect_and_backup_device, device_info, db_session)

                    if config_content:
                        # Create filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{device_name}_config_{timestamp}.cfg"

                        # Run the blocking FTP upload in a thread pool
                        with ThreadPoolExecutor() as executor:
                            success = await loop.run_in_executor(executor, upload_to_ftp, ftp_config, device_name, filename, config_content)

                        if success:
                            print(f"Successfully backed up {device_name} configuration to FTP as {filename}")
                            return device_name, True, None
                        else:
                            error_msg = f"Failed to upload {device_name} configuration to FTP"
                            print(error_msg)
                    else:
                        error_msg = f"Failed to retrieve configuration from {device_name}"
                        print(error_msg)

                except Exception as e:
                    error_msg = f"Error during backup of {device_name}: {str(e)}"
                    print(error_msg)

                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying backup for {device_name} (attempt {retry_count + 1}/{max_retries})...")
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff

            # If we reach here, all retries have failed
            error_msg = f"Failed to backup {device_name} after {max_retries} retries"
            print(error_msg)
            return device_name, False, error_msg

        # Create tasks for all devices to run in parallel
        tasks = []
        for device in devices:
            device_info = {
                'id': device.id,
                'name': device.name,
                'ip': device.ip_address,
                'device_type': device.device_type,
                'username': device.username,
                'password': device.password,
                'secret': device.secret,
                'port': device.port
            }
            task = async_connect_and_backup_device(device_info, device.name, ftp_config, db)
            tasks.append(task)
        
        # Run all tasks concurrently using a new event loop in a thread pool
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            finally:
                loop.close()
        
        # Process results
        successful_backups = 0
        failed_backups = 0
        backup_results = []

        for result in results:
            if isinstance(result, Exception):
                print(f"Task failed with exception: {result}")
                failed_backups += 1
                backup_results.append({
                    "status": "error",
                    "message": str(result)
                })
            else:
                device_name, success, error_msg = result
                if success:
                    successful_backups += 1
                    backup_results.append({
                        "device": device_name,
                        "status": "success"
                    })
                else:
                    failed_backups += 1
                    backup_results.append({
                        "device": device_name,
                        "status": "failed",
                        "message": error_msg
                    })

        return {
            "message": f"Backup process completed. Successful: {successful_backups}, Failed: {failed_backups}",
            "results": backup_results
        }
            
    except Exception as e:
        # Handle exceptions and update task state
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e  # Re-raise the exception to be caught by Celery worker
    finally:
        if db:
            db.close()

async def update_device_reachability_status():
    """
    Background task to periodically check device reachability and update the database.
    Performs checks asynchronously to avoid blocking.
    """
    db: Session = None
    try:
        db = SessionLocal()
        devices = crud.get_devices(db)
        
        # Create tasks for all device reachability checks
        tasks = []
        for db_device in devices:
            tasks.append(_check_and_update_device_reachability(db_device.id, db))
        
        # Run all checks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True) # Run and log exceptions
            
    finally:
        if db:
            db.close()

async def _check_and_update_device_reachability(device_id: int, db: Session):
    """
    Internal helper to check reachability for a single device and update its status in the database.
    """
    # Import the function from device_reachability module
    from .device_reachability import check_device_reachability
    
    # Call the function from device_reachability module which directly updates the database
    await check_device_reachability(device_id, db)


@celery_app.task
def cleanup_celery_meta():
    """
    Cleans up old Celery task metadata from the Redis backend to prevent it from growing indefinitely.
    """
    redis_client = Redis.from_url(settings.CELERY_RESULT_BACKEND)
    task_keys = list(redis_client.scan_iter("celery-task-meta-*"))
    
    if len(task_keys) > 100:
        tasks = []
        for key in task_keys:
            try:
                # The result is stored as a JSON string
                task_data = json.loads(redis_client.get(key))
                # Add the key to the task data for later deletion
                task_data['task_key'] = key
                tasks.append(task_data)
            except (json.JSONDecodeError, TypeError):
                # Handle cases where the key does not contain valid JSON or is None
                continue

        # Sort tasks by completion date, oldest first
        # We need to handle cases where 'date_done' might be missing
        tasks.sort(key=lambda x: x.get('date_done') or '1970-01-01T00:00:00.000000')

        # Calculate how many tasks to delete
        tasks_to_delete_count = len(tasks) - 25
        tasks_to_delete = tasks[:tasks_to_delete_count]
        
        for task in tasks_to_delete:
            redis_client.delete(task['task_key'])