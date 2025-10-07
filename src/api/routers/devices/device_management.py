import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .... import schemas
from ....config import settings
from ....crud import crud
from ....database import get_db
from ....device_reachability import check_device_reachability
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
    dependencies=[Depends(require_read_privileges)],
)
async def read_devices(
    skip: int = 0, limit: int = 5, db: Session = Depends(get_db)
):
    """
    Retrieve a list of network devices from the database, including their reachability status.
    Performs reachability checks asynchronously to avoid blocking.
    """
    db_devices = crud.get_devices(db, skip=skip, limit=limit)

    return db_devices 

@router.get(
    "/stats", response_model=Dict[str, int], dependencies=[Depends(require_read_privileges)]
)
async def get_device_stats(db: Session = Depends(get_db)):
    """  
    Get device statistics including total and active devices.

    Returns:
        Dict containing total_devices and active_devices
counts
    """
    devices = crud.get_devices(db)
    total_devices = len(devices)
    active_devices = sum(1 for i in devices if i.is_reachable)

    return {
        "total_devices": total_devices,
        "active_devices": active_devices,
        "inactive_devices": total_devices - active_devices,
    }

@router.get(
    "/{device_id}",
    response_model=schemas.DeviceDetail,
    dependencies=[Depends(require_read_privileges)],
)
async def read_device(device_id: int, db: Session = Depends(get_db)):
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

    updated_device = crud.update_device(db=db, device_id=device_id, device_update=device)

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

    return

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
    # Import the function from device_reachability module
    from ....device_reachability import check_device_reachability as check_reachability
    
    # Call the function from device_reachability module which directly updates the database
    is_reachable = await check_reachability(device_id, db)
    
    return is_reachable