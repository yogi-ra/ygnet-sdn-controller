from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....schemas import InterfaceState, InterfaceVlanConfig

from ...dependencies import require_read_privileges, require_write_privileges
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device Interfaces"])

@router.get(
    "/{device_id}/interfaces/brief", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_interfaces_brief(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get brief interface status information.
    """
    task = execute_netmiko_command_task.delay(device_id, "interfaces.get_interfaces_brief")
    return {"task_id": task.id}


@router.get(
    "/{device_id}/interfaces/status", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_interfaces_status(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get detailed interface status information.
    """
    task = execute_netmiko_command_task.delay(device_id, "interfaces.get_interfaces_status")
    return {"task_id": task.id}


@router.post(
    "/{device_id}/interfaces/state", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_write_privileges)]
)
def set_interface_state(
    device_id: int, interface_state: InterfaceState, db: Session = Depends(get_db)
):
    """
    Set interface state (up/down).
    """
    task = execute_netmiko_command_task.delay(
        device_id, 
        "interfaces.set_interface_state", 
        interface_state.interface_name, 
        interface_state.state
    )
    return {"task_id": task.id}


@router.post(
    "/{device_id}/interfaces/vlan-config", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_write_privileges)]
)
def configure_interface_vlan(
    device_id: int, interface_config: InterfaceVlanConfig, db: Session = Depends(get_db)
):
    """
    Configure VLAN settings for a specific interface (access or trunk mode).
    """
    task = execute_netmiko_command_task.delay(
        device_id, 
        "interfaces.configure_interface_vlan", 
        interface_config.dict()
    )
    return {"task_id": task.id}
