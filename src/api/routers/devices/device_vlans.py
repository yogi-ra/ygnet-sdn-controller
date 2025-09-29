from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Dict
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
    Assign a port to a specific VLAN.
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
)
def configure_interface_vlan(
    device_id: int,
    interface_config: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Configures VLAN settings for a specific interface (access or trunk).
    """
    interface_name = interface_config.get("interface_name")
    vlan_mode = interface_config.get("mode")
    if interface_name is None or vlan_mode is None:
        raise HTTPException(
            status_code=400, detail="Missing required fields in request body"
        )
    task = execute_netmiko_command_task.delay(device_id, "vlans.configure_interface_vlan", interface_config)
    return {"task_id": task.id}

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