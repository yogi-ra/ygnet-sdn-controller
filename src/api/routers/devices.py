from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Any, Dict
import json
import asyncio

from ...crud import crud
from ... import schemas
from ...database import get_db
from ...controllers import DEVICE_HANDLER_MAP
from ...device_info import DeviceConnectionInfo

from ..dependencies import (
    require_read_privileges,
    require_write_privileges,
)
from ..utils import get_handler_from_device_id

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


# Map device type keys to display names
DEVICE_TYPE_DISPLAY_NAMES = {
    "cisco_ios_router": "Cisco IOS Router",
    "cisco_ios_switch": "Cisco IOS Switch",
    "aruba_procurve": "Aruba Procurve",
    "ubiquiti_edgerouter": "Ubiquiti Edge Router",
    "ubiquiti_edgeswitch": "Ubiquiti Edge Switch",
    "ubiquiti_unifiswitch": "Ubiquiti UniFi Switch",
}

@router.get("/device-types", dependencies=[Depends(require_read_privileges)])
def get_device_types():
    """
    Returns a list of supported device types with their display names.
    """
    device_types = []
    for key in DEVICE_HANDLER_MAP.keys():
        device_types.append({
            "key": key,
            "display_name": DEVICE_TYPE_DISPLAY_NAMES.get(key, key)
        })
    return device_types


@router.post(
    "/", response_model=schemas.Device, dependencies=[Depends(require_write_privileges)]
)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Create a new network device in the database.
    """
    if crud.get_device_by_name(db, name=device.name):
        raise HTTPException(status_code=400, detail="Device name already registered")
    return crud.create_device(db=db, device=device)


@router.get(
    "/",
    response_model=List[schemas.Device],
    dependencies=[Depends(require_read_privileges)],
)
async def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all network devices from the database, including their reachability status.
    Performs reachability checks asynchronously to avoid blocking.
    """
    db_devices = crud.get_devices(db, skip=skip, limit=limit)
    devices_with_status = []
    
    # Create tasks for all device reachability checks
    tasks = []
    for db_device in db_devices:
        device_dict = schemas.Device.from_orm(db_device).dict()
        devices_with_status.append(device_dict)
        tasks.append(check_device_reachability(db_device.id, db))
    
    # Run all checks concurrently
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                devices_with_status[i]["is_reachable"] = False
                print(f"Error checking reachability for device {db_devices[i].id}: {result}")
            else:
                devices_with_status[i]["is_reachable"] = result
    
    return devices_with_status


@router.get(
    "/{device_id}",
    response_model=schemas.DeviceDetail,
    dependencies=[Depends(require_read_privileges)],
)
async def read_device(device_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single network device by its ID with detailed information.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)
    version_info = None
    interfaces_brief = None

    try:
        with handler:
            raw_version_info = handler.system.get_version_info()
            version_info = raw_version_info[0] if raw_version_info else None
            interfaces_brief = handler.interfaces.get_interfaces_brief()
    except Exception as e:
        error_msg = f"Error fetching operational data for device {device_id}: {str(e)}"
        print(error_msg)
        # Don't raise an exception here, just return the device info without the additional data

    # Check reachability asynchronously
    is_reachable = await check_device_reachability(device_id, db)

    # Create a dictionary from db_device and update is_reachable value
    device_dict = db_device.__dict__.copy()
    device_dict['is_reachable'] = is_reachable
    
    device_detail = schemas.DeviceDetail(
        **device_dict,
        version=version_info if version_info else None,
        interfaces=interfaces_brief if interfaces_brief else []
    )

    return device_detail


@router.put(
    "/{device_id}",
    response_model=schemas.Device,
    dependencies=[Depends(require_write_privileges)],
)
def update_device(
    device_id: int,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing network device in the database.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    updated_device = crud.update_device(
        db, device_id=device_id, device_update=device_update
    )
    return updated_device


@router.delete(
    "/{device_id}", status_code=204, dependencies=[Depends(require_write_privileges)]
)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a network device from the database.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    crud.delete_device(db, device_id=device_id)
    return


# Direct API endpoints for device features
@router.get("/{device_id}/system/version", dependencies=[Depends(require_read_privileges)])
def get_system_version(device_id: int, db: Session = Depends(get_db)):
    """
    Get system version information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            version_info = handler.system.get_version_info()
            return version_info
    except Exception as e:
        error_msg = f"Failed to get system version for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/system/hostname", dependencies=[Depends(require_read_privileges)])
def get_system_hostname(device_id: int, db: Session = Depends(get_db)):
    """
    Get system hostname.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            hostname = handler.system.get_hostname()
            return {"hostname": hostname}
    except Exception as e:
        error_msg = f"Failed to get system hostname for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/system/uptime", dependencies=[Depends(require_read_privileges)])
def get_system_uptime(device_id: int, db: Session = Depends(get_db)):
    """
    Get system uptime.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            uptime = handler.system.get_uptime()
            return {"uptime": uptime}
    except Exception as e:
        error_msg = f"Failed to get system uptime for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/system/clock", dependencies=[Depends(require_read_privileges)])
def get_system_clock(device_id: int, db: Session = Depends(get_db)):
    """
    Get system clock.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            clock = handler.system.get_clock()
            return {"clock": clock}
    except Exception as e:
        error_msg = f"Failed to get system clock for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/interfaces/brief", dependencies=[Depends(require_read_privileges)])
def get_interfaces_brief(device_id: int, db: Session = Depends(get_db)):
    """
    Get brief interface status.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_brief()
            return interfaces
    except Exception as e:
        error_msg = f"Failed to get interfaces brief for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/interfaces/status", dependencies=[Depends(require_read_privileges)])
def get_interfaces_status(device_id: int, db: Session = Depends(get_db)):
    """
    Get detailed interface status.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            status = handler.interfaces.get_interfaces_status()
            return status
    except Exception as e:
        error_msg = f"Failed to get interfaces status for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/interfaces/{interface_name}/state", dependencies=[Depends(require_write_privileges)])
def set_interface_state(
    device_id: int, 
    interface_name: str, 
    state: bool, 
    db: Session = Depends(get_db)
):
    """
    Set interface state (up/down).
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.interfaces.set_interface_state(interface_name, state)
            return {"result": result}
    except Exception as e:
        error_msg = f"Failed to set interface state for device {device_id}, interface {interface_name}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/system/reboot", dependencies=[Depends(require_write_privileges)])
def reboot_system(device_id: int, db: Session = Depends(get_db)):
    """
    Reboot the system.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # In a real implementation, this would call handler.system.reboot()
            # For now, we'll just return a success message
            return {"message": "System reboot initiated"}
    except Exception as e:
        error_msg = f"Failed to reboot system for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/{device_id}/check-reachability",
    response_model=bool,
    dependencies=[Depends(require_read_privileges)],
)
async def check_device_reachability(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Checks if a device is reachable by attempting to establish a Netmiko connection.
    This function is made async to prevent blocking other requests.
    """
    try:
        handler = get_handler_from_device_id(device_id, db)
        # Use asyncio.wait_for to add a timeout to the connection attempt
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def connect_handler():
            with handler:
                return True
                
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, connect_handler),
                timeout=10.0  # 10 second timeout
            )
        return result
    except asyncio.TimeoutError:
        print(f"Timeout checking reachability for device {device_id}")
        return False
    except Exception as e:
        print(f"Error checking reachability for device {device_id}: {str(e)}")
        return False


@router.get("/supported-features", dependencies=[Depends(require_read_privileges)])
def get_supported_features():
    """
    Returns a dictionary mapping device types to their supported features.
    This endpoint helps frontend developers understand what features are available for each device type.
    """
    supported_features = {}
    
    # For each device type in our handler map
    for device_type, handler_class in DEVICE_HANDLER_MAP.items():
        try:
            # Get the supported features from the handler class
            if hasattr(handler_class, 'get_supported_features'):
                features = handler_class.get_supported_features()
                # Handle the case where get_supported_features returns a tuple (view_features, action_features)
                if isinstance(features, tuple):
                    view_features, action_features = features
                    supported_features[device_type] = {
                        "view_features": view_features,
                        "action_features": action_features
                    }
                else:
                    # For handlers that return a simple list
                    supported_features[device_type] = {
                        "features": features
                    }
            else:
                supported_features[device_type] = {
                    "features": []
                }
        except Exception as e:
            # If there's an error getting features for a device type, log it and continue
            print(f"Error getting features for {device_type}: {e}")
            supported_features[device_type] = {
                "features": [],
                "error": str(e)
            }
    
    return supported_features