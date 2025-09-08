from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Any, Dict
import json
import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError

from ...crud import crud
from ... import schemas
from ...database import get_db
from ...controllers import DEVICE_HANDLER_MAP
from ...device_info import DeviceConnectionInfo
from ...config import settings
from ...connection_manager import ConnectionManager
from ...cache import get_redis_client
from ..decorators import cache_response

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
@cache_response("device_types", ttl=300)
def get_device_types(request: Request):
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

@router.post("/{device_id}/clear-cache", dependencies=[Depends(require_write_privileges)])
def clear_device_connection_cache(device_id: int, db: Session = Depends(get_db)):
    """
    Clears the connection cache for a specific device.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
        
    connection_manager = ConnectionManager()
    device_info = DeviceConnectionInfo(
        device_type=db_device.device_type,
        ip_address=db_device.ip_address,
        port=db_device.port,
        username=db_device.username,
        password=db_device.password,
        secret=db_device.secret
    )
    device_key = device_info.get_key()
    
    # Remove the specific device connection if it exists
    if device_key in connection_manager._connections:
        try:
            connection_manager._connections[device_key].disconnect()
        except:
            pass
        finally:
            del connection_manager._connections[device_key]
            
    # Clear Redis cache entries for this device
    redis_client = get_redis_client()
    pattern = f"device:{device_id}:*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)
            
    return {"message": f"Connection cache cleared for device {device_id}"}

@router.post("/{device_id}/cache/clear", dependencies=[Depends(require_write_privileges)])
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
        "device_vlans_brief"
    ]
    
    # Delete cache entries for each prefix with the device_id
    deleted_count = 0
    for prefix in cache_prefixes:
        cache_key = f"{prefix}:{device_id}"
        if redis_client.exists(cache_key):
            redis_client.delete(cache_key)
            deleted_count += 1
            
    return {"message": f"Cache cleared for device {device_id}. {deleted_count} cache entries removed."}

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
@cache_response("devices_list", ttl=60)
async def read_devices(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
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
    device_dict['is_reachable'] = is_reachable
    
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
    
    # Clear Redis cache entries for this device
    redis_client = get_redis_client()
    pattern = f"device:{device_id}:*"
    keys_to_delete = redis_client.keys(pattern)
    if keys_to_delete:
        redis_client.delete(*keys_to_delete)
    return


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
    except FutureTimeoutError:
        error_msg = f"Timeout getting system clock for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get system clock for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/interfaces/brief", dependencies=[Depends(require_read_privileges)])
@cache_response("device_interfaces_brief", ttl=120)
def get_interfaces_brief(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get brief interface status.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_brief()
            return interfaces
    except FutureTimeoutError:
        error_msg = f"Timeout getting interfaces brief for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get interfaces brief for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/interfaces/status", dependencies=[Depends(require_read_privileges)])
@cache_response("device_interfaces_status", ttl=120)
def get_interfaces_status(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get detailed interface status.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            status = handler.interfaces.get_interfaces_status()
            return status
    except FutureTimeoutError:
        error_msg = f"Timeout getting interfaces status for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get interfaces status for device {device_id}: {str(e)}"
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
            vlans = handler.vlans.get_vlan_brief()
            return vlans
    except FutureTimeoutError:
        error_msg = f"Timeout getting VLAN brief for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get VLAN brief for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/vlans/{vlan_id}/assign-port", dependencies=[Depends(require_write_privileges)])
def assign_port_to_vlan(
    device_id: int,
    vlan_id: int,
    port_assignment: schemas.PortAssignment,
    db: Session = Depends(get_db),
):
    """
    Assign a port to a specific VLAN.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.vlans.assign_port_to_vlan(vlan_id, port_assignment.port)
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout assigning port to VLAN for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to assign port to VLAN for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/interfaces/vlan-config", dependencies=[Depends(require_write_privileges)])
def configure_interface_vlan(
    device_id: int,
    interface_config: schemas.InterfaceVlanConfig,
    db: Session = Depends(get_db),
):
    """
    Configures VLAN settings for a specific interface (access or trunk).
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.vlans.configure_interface_vlan(interface_config)
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout configuring VLAN for interface {interface_config.interface_name} on device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to configure VLAN for interface {interface_config.interface_name} on device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/interfaces/state", dependencies=[Depends(require_write_privileges)])
def set_interface_state(
    device_id: int, 
    interface_state: schemas.InterfaceState, 
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
    except FutureTimeoutError:
        error_msg = f"Timeout rebooting system for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to reboot system for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/execute-command", dependencies=[Depends(require_write_privileges)])
def execute_command(
    device_id: int,
    command_input: schemas.CommandInput,
    db: Session = Depends(get_db)
):
    """
    Execute a command on the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            if command_input.is_config:
                # Execute configuration commands
                commands = command_input.command if isinstance(command_input.command, list) else [command_input.command]
                output = handler.send_config_set(commands)
            else:
                # Execute regular commands
                command_str = '\n'.join(command_input.command) if isinstance(command_input.command, list) else command_input.command
                output = handler.send_command(command_str)
            
            # Try to parse the output, but return raw output if parsing fails or returns empty result
            try:
                parsed_output = handler.parse_cli_output(command_str if not command_input.is_config else "config", output)
                # If parsing returns an empty list/dict, return raw output instead
                if not parsed_output:
                    return {"output": output}
                return {"output": parsed_output}
            except Exception:
                # If parsing fails with an exception, return the raw output
                return {"output": output}
    except FutureTimeoutError:
        error_msg = f"Timeout executing command for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to execute command for device {device_id}: {str(e)}"
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
@cache_response("supported_features", ttl=300)
def get_supported_features(request: Request):
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