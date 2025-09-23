from concurrent.futures import TimeoutError as FutureTimeoutError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import require_read_privileges
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device Routes"])


@router.get("/{device_id}/routing", dependencies=[Depends(require_read_privileges)])
@cache_response("device_routing_table", ttl=300)
def get_routing_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get routing table information.
    """
    task = execute_netmiko_command_task.delay(device_id, "routing.get_routing_table")
    return {"task_id": task.id}