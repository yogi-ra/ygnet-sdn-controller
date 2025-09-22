"""
Module for checking device reachability.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from .crud import crud
from .schemas import DeviceUpdate
from .exceptions import (
    DeviceTimeoutError,
    DeviceUnreachableError,
    DeviceConnectionError,
    DeviceAuthenticationError
)
from .config import settings
from .cache import get_redis_client
from .api.utils import get_handler_from_device_id


async def check_device_reachability(device_id: int, db: Session):
    """
    Asynchronously checks if a device is reachable.
    
    This function attempts to establish a connection to the device using its handler.
    It implements a timeout to prevent hanging connections and updates the device's
    reachability status in the database.
    """
    is_reachable = False
    try:
        db_device = crud.get_device(db, device_id=device_id)
        if not db_device:
            raise Exception("Device not found")

        handler = get_handler_from_device_id(device_id, db)
        
        # Use asyncio.wait_for to add a timeout to the connection attempt
        # The underlying ConnectionManager will use the fast TCP check.

        
        def connect_handler():
            with handler:
                return True
                
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, connect_handler),
                timeout=settings.NETMIKO_TIMEOUT # Use general Netmiko timeout
            )
        is_reachable = result
    except (asyncio.TimeoutError, DeviceTimeoutError):
        print(f"Timeout checking reachability for device {device_id}")
        is_reachable = False
    except (DeviceUnreachableError, DeviceConnectionError, DeviceAuthenticationError) as e:
        print(f"Error checking reachability for device {device_id}: {str(e)}")
        is_reachable = False
    except Exception as e:
        print(f"An unexpected error occurred during reachability check for device {device_id}: {str(e)}")
        is_reachable = False

    try:
        db_device = crud.get_device(db, device_id=device_id)  # Re-fetch to ensure fresh object
        if db_device and db_device.is_reachable != is_reachable:
            # Create a DeviceUpdate object to update the reachability status
            device_update = DeviceUpdate(is_reachable=is_reachable)
            crud.update_device(db, device_id, device_update)
            print(f"Updated reachability for device {device_id} to {is_reachable}")

            redis_client = get_redis_client()
            # Clear device detail cache
            cache_key = f"device_detail:{device_id}"
            if redis_client.exists(cache_key):
                redis_client.delete(cache_key)

    except Exception as e:
        print(f"Failed to update reachability status for device {device_id}: {str(e)}")
        
    return is_reachable