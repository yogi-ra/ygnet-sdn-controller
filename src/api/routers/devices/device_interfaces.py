from concurrent.futures import TimeoutError as FutureTimeoutError
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ....schemas import InterfaceState
from ...decorators import cache_response
from ...dependencies import require_read_privileges, require_write_privileges
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device Interfaces"])

@router.get(
    "/{device_id}/interfaces/brief", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_interfaces_brief", ttl=300)
def get_interfaces_brief(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get brief interface status information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_brief()
            return interfaces
    except Exception as e:
        error_msg = (
            f"Failed to get brief interface status for device {device_id}: {str(e)}"
        )
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/{device_id}/interfaces/status", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_interfaces_status", ttl=300)
def get_interfaces_status(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get detailed interface status information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            interfaces = handler.interfaces.get_interfaces_status()
            return interfaces
    except Exception as e:
        error_msg = (
            f"Failed to get detailed interface status for device {device_id}: {str(e)}"
        )
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post(
    "/{device_id}/interfaces/state", dependencies=[Depends(require_write_privileges)]
)
def set_interface_state(
    device_id: int, interface_state: InterfaceState, db: Session = Depends(get_db)
):
    """
    Set interface state (up/down).
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.interfaces.set_interface_state(
                interface_state.interface_name, interface_state.state
            )
            return {"result": result}
    except FutureTimeoutError:
        error_msg = f"Timeout setting interface state for device {device_id}, interface {interface_state.interface_name}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to set interface state for device {device_id}, interface {interface_state.interface_name}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
