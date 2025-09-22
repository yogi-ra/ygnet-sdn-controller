import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .... import schemas
from ....cache import get_redis_client
from ....config import settings
from ....crud import crud
from ....database import get_db
from ....device_reachability import check_device_reachability
from ....exceptions import (
    DeviceUnreachableError,
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError
)
from ...decorators import cache_response
from ...dependencies import require_read_privileges, require_write_privileges
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device Management"])

@router.post(
    "/", response_model=schemas.Device, dependencies=[Depends(require_write_privileges)]
)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Create a new network device in the database.
    """
    if crud.get_device_by_name(db, name=device.name):
        raise HTTPException(status_code=400, detail="Device name already registered")

    # Create the device
    created_device = crud.create_device(db=db, device=device)

    return created_device


@router.get(
    "/",
    response_model=List[schemas.Device],
    dependencies=[Depends(require_read_privileges)],
)
async def read_devices(
    request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Retrieve a list of network devices from the database, including their reachability status.
    Performs reachability checks asynchronously to avoid blocking.
    """
    db_devices = crud.get_devices(db, skip=skip, limit=limit)

    # Check reachability for all devices asynchronously
    reachability_tasks = [
        check_device_reachability(db_device.id, db) for db_device in db_devices
    ]
    reachability_results = await asyncio.gather(
        *reachability_tasks, return_exceptions=True
    )

    # Update device objects with reachability status
    devices_with_reachability = []
    for i, db_device in enumerate(db_devices):
        device_dict = db_device.__dict__.copy()
        # Handle potential exceptions in reachability checks
        if isinstance(reachability_results[i], Exception):
            device_dict["is_reachable"] = False
        else:
            device_dict["is_reachable"] = reachability_results[i]
        devices_with_reachability.append(schemas.Device(**device_dict))

    return devices_with_reachability


@router.get(
    "/{device_id}",
    response_model=schemas.DeviceDetail,
    dependencies=[Depends(require_read_privileges)],
)
@cache_response("device_detail", ttl=60)
async def read_device(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single network device by its ID with detailed information.
    Only includes version information. Interfaces and other operational data
    should be fetched lazily by the frontend as needed.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)
    version_info = None

    try:
        with handler:
            raw_version_info = handler.system.get_version_info()
            version_info = raw_version_info[0] if raw_version_info else None
    except Exception as e:
        error_msg = f"Error fetching version info for device {device_id}: {str(e)}"
        print(error_msg)
        # Don't raise an exception here, just return the device info without the additional data

    # Check reachability asynchronously
    is_reachable = await check_device_reachability(device_id, db)

    # Create a dictionary from db_device and update is_reachable value
    device_dict = db_device.__dict__.copy()
    device_dict["is_reachable"] = is_reachable

    device_detail = schemas.DeviceDetail(
        **device_dict,
        version=version_info if version_info else None,
    )

    return device_detail


@router.put(
    "/{device_id}",
    response_model=schemas.Device,
    dependencies=[Depends(require_write_privileges)],
)
def update_device(
    device_id: int, device: schemas.DeviceUpdate, db: Session = Depends(get_db)
):
    """
    Update a network device in the database.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    updated_device = crud.update_device(db=db, device_id=device_id, device=device)

    # Clear Redis cache entries for this device
    redis_client = get_redis_client()
    pattern = f"device:{device_id}:*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

    return updated_device


@router.delete("/{device_id}", dependencies=[Depends(require_write_privileges)])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """
    Delete a network device from the database.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    crud.delete_device(db, device_id=device_id)

    # Clear Redis cache entries for this device
    redis_client = get_redis_client()
    pattern = f"device:{device_id}:*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

    return


@router.post(
    "/{device_id}/cache/clear", dependencies=[Depends(require_write_privileges)]
)
def clear_device_cache(device_id: int, db: Session = Depends(get_db)):
    """
    Clears the Redis cache for a specific device.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    # Clear Redis cache entries for this device
    redis_client = get_redis_client()

    # List of cache prefixes used in device endpoints
    cache_prefixes = [
        "device_detail",
        "device_system_version",
        "device_system_hostname",
        "device_system_uptime",
        "device_system_clock",
        "device_interfaces_brief",
        "device_interfaces_status",
        "device_vlans_brief",
        "device_arp_table",
        "device_cdp_neighbors",
        "device_lldp_neighbors",
    ]

    # Delete cache entries for each prefix with the device_id
    deleted_count = 0
    for prefix in cache_prefixes:
        cache_key = f"{prefix}:{device_id}"
        if redis_client.exists(cache_key):
            redis_client.delete(cache_key)
            deleted_count += 1

    return {
        "message": f"Cache cleared for device {device_id}. {deleted_count} cache entries removed."
    }


@router.get(
    "/{device_id}/check-reachability", dependencies=[Depends(require_read_privileges)]
)
async def check_device_reachability(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Checks if a device is reachable by attempting to establish a Netmiko connection.
    This function is made async to prevent blocking other requests.
    It updates the device's reachability status in the database.
    """
    is_reachable = False
    try:
        db_device = crud.get_device(db, device_id=device_id)
        if not db_device:
            raise HTTPException(status_code=404, detail="Device not found")

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
                timeout=settings.NETMIKO_TIMEOUT,  # Use general Netmiko timeout
            )
        is_reachable = result
    except (asyncio.TimeoutError, DeviceTimeoutError):
        print(f"Timeout checking reachability for device {device_id}")
        is_reachable = False
    except (
        DeviceUnreachableError,
        DeviceConnectionError,
        DeviceAuthenticationError,
    ) as e:
        print(f"Error checking reachability for device {device_id}: {str(e)}")
        is_reachable = False
    except Exception as e:
        print(
            f"An unexpected error occurred during reachability check for device {device_id}: {str(e)}"
        )
        is_reachable = False

    try:
        # Re-fetch to ensure fresh object
        db_device = crud.get_device(db, device_id=device_id)
        if db_device and db_device.is_reachable != is_reachable:
            # Create a DeviceUpdate object to update the reachability status
            device_update = schemas.DeviceUpdate(is_reachable=is_reachable)
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
