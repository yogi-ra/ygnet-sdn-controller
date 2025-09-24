import asyncio
import socket
from sqlalchemy.orm import Session
from redis import Redis

from src.celery_app import celery_app
from src.schemas import DeviceUpdate
from src.crud import crud
from src.database import SessionLocal

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