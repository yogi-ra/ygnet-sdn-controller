import asyncio
import socket
from sqlalchemy.orm import Session
from redis import Redis

from src.celery_app import celery_app
from src.schemas import DeviceUpdate
from src.crud import crud
from src.database import SessionLocal
from src.cache import get_redis_client
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


async def check_device_for_changes():
    """
    Background task to periodically check devices for changes and invalidate cache.
    """
    db: Session = None
    redis_client: Redis = None
    try:
        db = SessionLocal()
        redis_client = get_redis_client()

        devices = crud.get_devices(db)  # Fetch all devices

        for device in devices:
            cache_key = f"device:{device.id}:details"
            # For simplicity, let's check version info for changes
            # A more robust solution would involve hashing running config
            try:
                handler = get_handler_from_device_id(device.id, db)
                with handler:
                    current_version = handler.system.get_version_info()

                # In a real scenario, you'd compare this to a stored 'last_known_version'
                # For now, we'll just invalidate if we successfully get a version.
                # Or, more accurately, we'd store the version in the DB and compare.
                if current_version:
                    print(
                        f"Device {device.name} (ID: {device.id}) version fetched. Invalidating cache."
                    )
                    redis_client.delete(cache_key)

            except Exception as e:
                print(
                    f"Error checking device {device.name} (ID: {device.id}) for changes: {e}"
                )

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
    is_reachable = False
    redis_client = get_redis_client()
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        print(f"Device with ID {device_id} not found in DB, skipping reachability check.")
        return

    # Fast TCP check to quickly identify offline devices
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Short timeout for the check
    is_port_open = sock.connect_ex((db_device.ip_address, db_device.port)) == 0
    sock.close()

    if not is_port_open:
        # If the port is not open, we can be sure it's unreachable
        is_reachable = False
        print(f"Device {db_device.name} (ID: {db_device.id}) is not reachable (port closed).")
    else:
        # If port is open, proceed with the full connection check
        try:
            handler = get_handler_from_device_id(db_device.id, db)
            with handler:
                # If connection is successful, it's reachable
                is_reachable = True
        except (DeviceUnreachableError, DeviceTimeoutError, DeviceConnectionError, DeviceAuthenticationError) as e:
            print(f"Device {db_device.name} (ID: {db_device.id}) is not reachable: {e}")
            is_reachable = False
        except Exception as e:
            print(f"An unexpected error occurred for device {db_device.name} (ID: {db_device.id}): {e}")
            is_reachable = False
    
    # Update the device's reachability status in the database
    try:
        db_device = crud.get_device(db, device_id=device_id)  # Re-fetch to ensure fresh object
        if db_device and db_device.is_reachable != is_reachable:
            # Create a DeviceUpdate object to update the reachability status
            device_update = DeviceUpdate(is_reachable=is_reachable)
            crud.update_device(db, device_id, device_update)
            print(f"Updated reachability for device {device_id} to {is_reachable}")

            # Invalidate all caches related to this device
            pattern = f"device:{db_device.id}:*"
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)
            print(
                f"Invalidated cache for device {db_device.name} (ID: {db_device.id}) due to reachability status change."
            )

    except Exception as e:
        print(f"Failed to update reachability status for device {device_id}: {str(e)}")