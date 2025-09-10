from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from concurrent.futures import TimeoutError as FutureTimeoutError
from ....crud import crud
from ....database import get_db
from ....cache import get_redis_client
from ....exceptions import DeviceUnreachableError, DeviceConnectionError, DeviceAuthenticationError, DeviceTimeoutError
from ...decorators import cache_response
from ...dependencies import (
    require_read_privileges,
    require_write_privileges,
)
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device VLANs"])

@router.post("/{device_id}/vlans/{vlan_id}/assign-port", dependencies=[Depends(require_write_privileges)])
def assign_port_to_vlan(
    device_id: int,
    vlan_id: int,
    port_assignment: Dict[str, str],
    db: Session = Depends(get_db),
):
    """
    Assign a port to a specific VLAN.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Extract the port from the request body
            port = port_assignment.get("port")
            if port is None:
                raise HTTPException(status_code=400, detail="Missing 'port' field in request body")
            
            result = handler.vlans.assign_port_to_vlan(vlan_id, port)
            
            # Clear cache for this device's VLAN information
            redis_client = get_redis_client()
            redis_client.delete(f"device_vlans_brief:{device_id}")
            
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
    interface_config: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Configures VLAN settings for a specific interface (access or trunk).
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Extract interface configuration from request body
            interface_name = interface_config.get("interface_name")
            vlan_mode = interface_config.get("vlan_mode")
            vlan_ids = interface_config.get("vlan_ids")
            
            if interface_name is None or vlan_mode is None:
                raise HTTPException(status_code=400, detail="Missing required fields in request body")
            
            result = handler.vlans.configure_interface_vlan(interface_config)
            
            # Clear cache for this device's VLAN and interface information
            redis_client = get_redis_client()
            redis_client.delete(f"device_vlans_brief:{device_id}")
            redis_client.delete(f"device_interfaces_brief:{device_id}")
            redis_client.delete(f"device_interfaces_status:{device_id}")
            
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout configuring VLAN for interface {interface_config.get('interface_name')} on device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to configure VLAN for interface {interface_config.get('interface_name')} on device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)