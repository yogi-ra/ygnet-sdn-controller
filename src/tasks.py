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