from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...dependencies import (
    require_read_privileges,
)
from ....tasks import execute_netmiko_command_task

router = APIRouter(tags=["Device Discovery"])

# API endpoints for device discovery features


@router.get("/{device_id}/arp", dependencies=[Depends(require_read_privileges)])
def get_arp_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get ARP table information.
    """
    task = execute_netmiko_command_task.delay(device_id, "arp.get_arp_interface")
    return {"task_id": task.id}

@router.get("/{device_id}/cdp", dependencies=[Depends(require_read_privileges)])
def get_cdp_neighbors(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get CDP neighbors information.
    """
    task = execute_netmiko_command_task.delay(device_id, "cdp.get_cdp_neighbors")
    return {"task_id": task.id}

@router.get("/{device_id}/lldp", dependencies=[Depends(require_read_privileges)])
def get_lldp_neighbors(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get LLDP neighbors information.
    """
    task = execute_netmiko_command_task.delay(device_id, "lldp.get_lldp_neighbors")
    return {"task_id": task.id}