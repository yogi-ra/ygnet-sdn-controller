from concurrent.futures import TimeoutError as FutureTimeoutError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...dependencies import require_read_privileges
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device Routes"])


@router.get("/{device_id}/routing", dependencies=[Depends(require_read_privileges)])
def get_routing_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get routing table information.
    """
    task = execute_netmiko_command_task.delay(device_id, "routing.get_routing_table")
    return {"task_id": task.id}


@router.post("/{device_id}/execute-command", dependencies=[Depends(require_read_privileges)])
def execute_command(request: Request, device_id: int, command: dict, db: Session = Depends(get_db)):
    """
    Execute a command on the device.
    """
    cmd = command.get("command")
    is_config = command.get("is_config", False)
    
    if not cmd:
        raise HTTPException(status_code=400, detail="Command is required")
    
    # Determine the appropriate method based on command type
    method = "system.execute_config_command" if is_config else "system.execute_command"
    
    task = execute_netmiko_command_task.delay(device_id, method, cmd)
    return {"task_id": task.id}