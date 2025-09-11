from concurrent.futures import TimeoutError as FutureTimeoutError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import require_read_privileges
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device Routes"])


@router.get("/{device_id}/routing", dependencies=[Depends(require_read_privileges)])
@cache_response("device_routing_table", ttl=300)
def get_routing_table(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get routing table information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            routing_table = handler.routing.get_routing_table()
            return routing_table
    except FutureTimeoutError:
        error_msg = f"Timeout getting routing table for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to get routing table for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
