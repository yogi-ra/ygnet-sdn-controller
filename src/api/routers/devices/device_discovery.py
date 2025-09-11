from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import (
    require_read_privileges,
)
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device Discovery"])

# API endpoints for device discovery features


@router.get("/{device_id}/arp", dependencies=[Depends(require_read_privileges)])
@cache_response("device_arp_table", ttl=300)
def get_arp_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get ARP table information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            arp_table = handler.arp.get_arp_interface()
            return arp_table
    except Exception as e:
        error_msg = f"Failed to get ARP table for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/cdp", dependencies=[Depends(require_read_privileges)])
@cache_response("device_cdp_neighbors", ttl=300)
def get_cdp_neighbors(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get CDP neighbors information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            cdp_neighbors = handler.cdp.get_cdp_neighbors()
            return cdp_neighbors
    except Exception as e:
        error_msg = f"Failed to get CDP neighbors for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{device_id}/lldp", dependencies=[Depends(require_read_privileges)])
@cache_response("device_lldp_neighbors", ttl=300)
def get_lldp_neighbors(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get LLDP neighbors information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            lldp_neighbors = handler.lldp.get_lldp_neighbors()
            return lldp_neighbors
    except Exception as e:
        error_msg = f"Failed to get LLDP neighbors for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

