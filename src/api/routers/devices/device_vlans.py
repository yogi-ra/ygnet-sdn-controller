from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....cache import get_redis_client
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import require_read_privileges, require_write_privileges
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device VLANs"])

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
            if not hasattr(handler, "vlans"):
                raise HTTPException(
                    status_code=400, detail="Device does not support VLANs"
                )

            vlans = handler.vlans.get_vlan_brief()
            return vlans
    except Exception as e:
        error_msg = f"Failed to get VLAN information for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{device_id}/vlans", dependencies=[Depends(require_write_privileges)])
def create_vlan(
    device_id: int, vlan_data: Dict[str, Any], db: Session = Depends(get_db)
):
    """
    Create a new VLAN on the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Check if the device supports VLANs
            if not hasattr(handler, "vlans"):
                raise HTTPException(
                    status_code=400, detail="Device does not support VLANs"
                )

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


@router.post(
    "/{device_id}/vlans/{vlan_id}/assign-port",
    dependencies=[Depends(require_write_privileges)],
)
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
                raise HTTPException(
                    status_code=400, detail="Missing 'port' field in request body"
                )

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


@router.post(
    "/{device_id}/vlans/{vlan_id}/change-name",
    dependencies=[Depends(require_write_privileges)],
)
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
                raise HTTPException(
                    status_code=400, detail="Missing 'new_name' field in request body"
                )

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


@router.post(
    "/{device_id}/interfaces/vlan-config",
    dependencies=[Depends(require_write_privileges)],
)
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
                raise HTTPException(
                    status_code=400, detail="Missing required fields in request body"
                )

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


@router.delete(
    "/{device_id}/vlans/{vlan_id}",
    dependencies=[Depends(require_write_privileges)],
)
def delete_vlan(
    device_id: int,
    vlan_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a VLAN from the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            # Check if the device supports VLANs
            if not hasattr(handler, "vlans"):
                raise HTTPException(
                    status_code=400, detail="Device does not support VLANs"
                )

            result = handler.vlans.delete_vlan(vlan_id)

            # Clear cache for this device's VLAN information
            redis_client = get_redis_client()
            redis_client.delete(f"device_vlans_brief:{device_id}")

            return {"result": result}
    except Exception as e:
        error_msg = f"Failed to delete VLAN for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

