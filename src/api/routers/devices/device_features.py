from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Any, Dict
import json
import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError, ThreadPoolExecutor
from ....crud import crud
from ....database import get_db
from ....device_info import DeviceConnectionInfo
from ....config import settings
from ....connection_manager import ConnectionManager
from ....cache import get_redis_client
from ....schemas import DeviceUpdate, InterfaceState
from ....exceptions import DeviceUnreachableError, DeviceConnectionError, DeviceAuthenticationError, DeviceTimeoutError
from ...decorators import cache_response
from ...dependencies import (
    require_read_privileges,
    require_write_privileges,
)
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device Features"])

# Direct API endpoints for device features
@router.get("/{device_id}/system/version", dependencies=[Depends(require_read_privileges)])
@cache_response("device_system_version", ttl=300)
def get_system_version(request: Request, device_id: int, db: Session = Depends(get_db)):
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
@cache_response("device_system_hostname", ttl=300)
def get_system_hostname(request: Request, device_id: int, db: Session = Depends(get_db)):
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
@cache_response("device_system_uptime", ttl=300)
def get_system_uptime(request: Request, device_id: int, db: Session = Depends(get_db)):
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
@cache_response("device_system_clock", ttl=300)
def get_system_clock(request: Request, device_id: int, db: Session = Depends(get_db)):
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
@cache_response("device_interfaces_brief", ttl=300)
def get_interfaces_brief(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get brief interface status information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_brief()
            return interfaces
    except Exception as e:
        error_msg = f"Failed to get brief interface status for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{device_id}/interfaces/status", dependencies=[Depends(require_read_privileges)])
@cache_response("device_interfaces_status", ttl=300)
def get_interfaces_status(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get detailed interface status information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_status()
            return interfaces
    except Exception as e:
        error_msg = f"Failed to get detailed interface status for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{device_id}/interfaces/state", dependencies=[Depends(require_write_privileges)])
def set_interface_state(
    device_id: int,
    interface_state: InterfaceState,
    db: Session = Depends(get_db)
):
    """
    Set interface state (up/down).
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.interfaces.set_interface_state(interface_state.interface_name, interface_state.state)
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout setting interface state for device {device_id}, interface {interface_state.interface_name}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to set interface state for device {device_id}, interface {interface_state.interface_name}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{device_id}/vlans/brief", dependencies=[Depends(require_read_privileges)])
@cache_response("device_vlans_brief", ttl=300)
def get_vlans_brief(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get brief VLAN information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Check if the device supports VLANs
            if not hasattr(handler, 'vlans'):
                raise HTTPException(status_code=400, detail="Device does not support VLANs")
            
            vlans = handler.vlans.get_vlan_brief()
            return vlans
    except Exception as e:
        error_msg = f"Failed to get VLAN information for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{device_id}/vlans", dependencies=[Depends(require_write_privileges)])
def create_vlan(device_id: int, vlan_data: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Create a new VLAN on the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Check if the device supports VLANs
            if not hasattr(handler, 'vlans'):
                raise HTTPException(status_code=400, detail="Device does not support VLANs")
            
            # Extract VLAN ID and optional name from request
            vlan_id = vlan_data.get("id")
            vlan_name = vlan_data.get("name")
            
            if vlan_id is None:
                raise HTTPException(status_code=400, detail="Missing VLAN ID")
            
            result = handler.vlans.create_vlan(vlan_id, vlan_name)
            
            # Clear cache for this device's VLAN information
            redis_client = get_redis_client()
            redis_client.delete(f"device_vlans_brief:{device_id}")
            
            return result
    except Exception as e:
        error_msg = f"Failed to create VLAN for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{device_id}/system/reboot", dependencies=[Depends(require_write_privileges)])
def reboot_device(device_id: int, db: Session = Depends(get_db)):
    """
    Reboot the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.system.reboot()
            return result
    except Exception as e:
        error_msg = f"Failed to reboot device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{device_id}/check-reachability", dependencies=[Depends(require_read_privileges)])
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
                timeout=settings.NETMIKO_TIMEOUT # Use general Netmiko timeout
            )
        is_reachable = result
    except (asyncio.TimeoutError, FutureTimeoutError, DeviceTimeoutError):
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
            
            # Clear devices list cache to ensure device list reflects updated reachability
            devices_list_cache_key = "devices_list"
            if redis_client.exists(devices_list_cache_key):
                redis_client.delete(devices_list_cache_key)
    except Exception as e:
        print(f"Failed to update reachability status for device {device_id}: {str(e)}")
    
    return is_reachable

@router.get("/{device_id}/routing", dependencies=[Depends(require_read_privileges)])
@cache_response("device_routing_table", ttl=300)
def get_routing_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get routing table information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            routing_table = handler.routing.get_routing_table()
            return routing_table
    except FutureTimeoutError:
        error_msg = f"Timeout getting routing table for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get routing table for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{device_id}/vlans/{vlan_id}/change-name", dependencies=[Depends(require_write_privileges)])
def change_vlan_name(
    device_id: int,
    vlan_id: int,
    vlan_name_change: Dict[str, str],
    db: Session = Depends(get_db),
):
    """
    Change the name of a VLAN.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Extract the new name from the request body
            new_name = vlan_name_change.get("new_name")
            if new_name is None:
                raise HTTPException(status_code=400, detail="Missing 'new_name' field in request body")
            
            result = handler.vlans.change_vlan_name(vlan_id, new_name)
            
            # Clear cache for this device's VLAN information
            redis_client = get_redis_client()
            redis_client.delete(f"device_vlans_brief:{device_id}")
            
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout changing VLAN name for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to change VLAN name for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)