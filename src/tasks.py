import asyncio
from sqlalchemy.orm import Session
from redis import Redis

from .crud import crud
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
                # For now, we'll just invalidate if we can fetch it, assuming any fetch implies potential change
                # Or, more accurately, we'd store the version in the DB and compare.
                # For demonstration, let's just invalidate if we successfully get a version.
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


async def check_single_device_reachability(device_id, db):
    """
    Check reachability for a single device asynchronously.
    """
    is_reachable = False
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        print(f"Device with ID {device_id} not found in DB, skipping reachability check.")
        return

    try:
        handler = get_handler_from_device_id(db_device.id, db)
        with handler:
            # If connection is successful, it's reachable
            is_reachable = True
    except Exception as e:
        print(f"Device {db_device.name} (ID: {db_device.id}) is not reachable: {e}")
        is_reachable = False
    
    return db_device, is_reachable


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
        tasks = [
            check_single_device_reachability(device_schema.id, db) 
            for device_schema in devices
        ]
        
        # Run all checks concurrently with a timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        redis_client = get_redis_client()
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                print(f"Error during device reachability check: {result}")
                continue
                
            if result is None:
                continue
                
            db_device, is_reachable = result
            
            # Update the device's reachability status in the database
            if db_device.is_reachable != is_reachable:  # Only update if status changed
                db_device.is_reachable = is_reachable
                db.commit()
                db.refresh(db_device)
                print(
                    f"Updated reachability for device {db_device.name} (ID: {db_device.id}) to {is_reachable}"
                )
                
                # Invalidate all caches related to this device
                for key in redis_client.scan_iter(f"device:{db_device.id}:*"):
                    redis_client.delete(key)
                print(
                    f"Invalidated cache for device {db_device.name} (ID: {db_device.id}) due to reachability status change."
                )
    finally:
        if db:
            db.close()