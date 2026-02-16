from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ....database import get_db
from ...dependencies import require_read_privileges, require_write_privileges
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device VLANs"])

@router.get("/{device_id}/vlans/brief", 
            status_code=status.HTTP_202_ACCEPTED,
            dependencies=[Depends(require_read_privileges)])
def get_vlans_brief(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get brief VLAN information.
    """
    task = execute_netmiko_command_task.delay(device_id, "vlans.get_vlan_brief")
    return {"task_id": task.id}

@router.get("/{device_id}/vlans/port-config",
            status_code=status.HTTP_202_ACCEPTED,
            dependencies=[Depends(require_read_privileges)])
def get_vlan_port_configuration(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get VLAN configuration for all ports (Access/Trunk mode, Native VLAN, Allowed VLANs).
    """
    task = execute_netmiko_command_task.delay(device_id, "vlans.get_port_vlan_config")
    return {"task_id": task.id}

@router.post("/{device_id}/vlans", dependencies=[Depends(require_write_privileges)])
def create_vlan(
    device_id: int, vlan_data: Dict[str, Any], db: Session = Depends(get_db)
):
    """
    Create a new VLAN on the device.
    """
    vlan_id = vlan_data.get("id")
    vlan_name = vlan_data.get("name")
    if vlan_id is None:
        raise HTTPException(status_code=400, detail="Missing VLAN ID")
    task = execute_netmiko_command_task.delay(device_id, "vlans.create_vlan", vlan_id, vlan_name)
    return {"task_id": task.id}

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
    Assign a port to a specific VLAN (Access mode).
    """
    port = port_assignment.get("port")
    if port is None:
        raise HTTPException(
            status_code=400, detail="Missing 'port' field in request body"
        )
    task = execute_netmiko_command_task.delay(device_id, "vlans.assign_port_to_vlan", vlan_id, port)
    return {"task_id": task.id}

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
    new_name = vlan_name_change.get("new_name")
    if new_name is None:
        raise HTTPException(
            status_code=400, detail="Missing 'new_name' field in request body"
        )
    task = execute_netmiko_command_task.delay(device_id, "vlans.change_vlan_name", vlan_id, new_name)
    return {"task_id": task.id}

@router.post(
    "/{device_id}/interfaces/vlan-config",
    dependencies=[Depends(require_write_privileges)],
    status_code=status.HTTP_202_ACCEPTED
)
def configure_interface_vlan(
    device_id: int,
    interface_config: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Configures VLAN settings for multiple interfaces.
    """
    configs = interface_config.get("configs")
    
    if configs is None or not isinstance(configs, list):
        raise HTTPException(
            status_code=400, 
            detail="Missing or invalid 'configs' field in request body. Expected array of interface configurations."
        )
    
    if len(configs) == 0:
        raise HTTPException(
            status_code=400, 
            detail="'configs' array cannot be empty"
        )
    
    for idx, config in enumerate(configs):
        if not config.get("interface_name"):
            raise HTTPException(
                status_code=400, 
                detail=f"Config at index {idx} missing 'interface_name' field"
            )
        if not config.get("mode"):
            raise HTTPException(
                status_code=400, 
                detail=f"Config at index {idx} missing 'mode' field"
            )
        
        mode = config["mode"].lower()
        if mode == "access" and not config.get("access_vlan"):
            raise HTTPException(
                status_code=400, 
                detail=f"Access mode config at index {idx} missing 'access_vlan' field"
            )
        elif mode == "trunk":
            if not config.get("allowed_vlans") and not config.get("native_vlan"):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Trunk mode config at index {idx} must have at least one of 'allowed_vlans' or 'native_vlan'"
                )
    
    for config in configs:
        task = execute_netmiko_command_task.delay(
            device_id, 
            "vlans.configure_interface_vlan", 
            config 
        )
    
    return {
        "task_id": task.id,
    }

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
    task = execute_netmiko_command_task.delay(device_id, "vlans.delete_vlan", vlan_id)
    return {"task_id": task.id}