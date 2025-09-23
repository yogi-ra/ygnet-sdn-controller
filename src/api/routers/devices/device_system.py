from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import require_read_privileges, require_write_privileges
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device System"])

@router.get(
    "/{device_id}/system/version", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_system_version(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system version information.
    """
    task = execute_netmiko_command_task.delay(device_id, "system.get_version_info")
    return {"task_id": task.id}


@router.get(
    "/{device_id}/system/hostname", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_system_hostname(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get system hostname.
    """
    task = execute_netmiko_command_task.delay(device_id, "system.get_hostname")
    return {"task_id": task.id}


@router.post(
    "/{device_id}/system/reboot", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_write_privileges)]
)
def reboot_device(device_id: int, db: Session = Depends(get_db)):
    """
    Reboot the device.
    """
    task = execute_netmiko_command_task.delay(device_id, "system.reboot")
    return {"task_id": task.id}


@router.get(
    "/{device_id}/system/uptime", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_system_uptime(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system uptime.
    """
    task = execute_netmiko_command_task.delay(device_id, "system.get_uptime")
    return {"task_id": task.id}


@router.get(
    "/{device_id}/system/clock", 
    status_code=status.HTTP_202_ACCEPTED, 
    dependencies=[Depends(require_read_privileges)]
)
def get_system_clock(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system clock.
    """
    task = execute_netmiko_command_task.delay(device_id, "system.get_clock")
    return {"task_id": task.id}

