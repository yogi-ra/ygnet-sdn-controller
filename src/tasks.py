import asyncio
from sqlalchemy.orm import Session
from redis import Redis

from . import crud, schemas
from .database import SessionLocal
from .cache import get_redis_client
from .api.utils import get_handler_from_device_id

async def check_device_for_changes():
    """
    Background task to periodically check devices for changes and invalidate cache.
    """
    db: Session = None
    redis_client: Redis = None
    try:
        db = SessionLocal()
        redis_client = get_redis_client()

        devices = crud.get_devices(db) # Fetch all devices

        for device in devices:
            cache_key = f"device:{device.id}:details"
            # For simplicity, let's check version info for changes
            # A more robust solution would involve hashing running config
            try:
                handler = get_handler_from_device_id(device.id, db)
                with handler:
                    current_version = handler.get_version_info()

                # In a real scenario, you'd compare this to a stored 'last_known_version'
                # For now, we'll just invalidate if we can fetch it, assuming any fetch implies potential change
                # Or, more accurately, we'd store the version in the DB and compare.
                # For demonstration, let's just invalidate if we successfully get a version.
                if current_version:
                    print(f"Device {device.name} (ID: {device.id}) version fetched. Invalidating cache.")
                    redis_client.delete(cache_key)

            except Exception as e:
                print(f"Error checking device {device.name} (ID: {device.id}) for changes: {e}")

    finally:
        if db:
            db.close()

from .database import get_db # New import
from .models import NetworkDevice # New import

async def update_device_reachability_status():
    """
    Background task to periodically check device reachability and update the database.
    """
    db: Session = None
    try:
        db = SessionLocal()
        devices = crud.get_devices(db)

        for device in devices:
            is_reachable = False
            try:
                handler = get_handler_from_device_id(device.id, db)
                with handler:
                    # If connection is successful, it's reachable
                    is_reachable = True
            except Exception as e:
                print(f"Device {device.name} (ID: {device.id}) is not reachable: {e}")
                is_reachable = False
            finally:
                # Update the device's reachability status in the database
                if device.is_reachable != is_reachable: # Only update if status changed
                    device.is_reachable = is_reachable
                    db.add(device)
                    db.commit()
                    db.refresh(device)
                    print(f"Updated reachability for device {device.name} (ID: {device.id}) to {is_reachable}")
    finally:
        if db:
            db.close()

