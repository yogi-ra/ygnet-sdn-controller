from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ....database import get_db
from ...decorators import cache_response
from ...dependencies import require_read_privileges, require_write_privileges
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device System"])

@router.get(
    "/{device_id}/system/version", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_system_version", ttl=300)
def get_system_version(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system version information.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            version_info = handler.system.get_version_info()
            return version_info
    except Exception as e:
        error_msg = f"Failed to get system version for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/{device_id}/system/hostname", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_system_hostname", ttl=300)
def get_system_hostname(
    request: Request, device_id: int, db: Session = Depends(get_db)
):
    """
    Get system hostname.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            hostname = handler.system.get_hostname()
            return {"hostname": hostname}
    except Exception as e:
        error_msg = f"Failed to get system hostname for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post(
    "/{device_id}/system/reboot", dependencies=[Depends(require_write_privileges)]
)
def reboot_device(device_id: int, db: Session = Depends(get_db)):
    """
    Reboot the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            result = handler.system.reboot()
            return result
    except Exception as e:
        error_msg = f"Failed to reboot device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/{device_id}/system/uptime", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_system_uptime", ttl=300)
def get_system_uptime(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system uptime.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            uptime = handler.system.get_uptime()
            return {"uptime": uptime}
    except Exception as e:
        error_msg = f"Failed to get system uptime for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get(
    "/{device_id}/system/clock", dependencies=[Depends(require_read_privileges)]
)
@cache_response("device_system_clock", ttl=300)
def get_system_clock(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Get system clock.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            clock = handler.system.get_clock()
            return {"clock": clock}
    except Exception as e:
        error_msg = f"Failed to get system clock for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post(
    "/{device_id}/execute-command", dependencies=[Depends(require_write_privileges)]
)
def execute_command(
    device_id: int, command_input: Dict[str, Any], db: Session = Depends(get_db)
):
    """
    Execute a command on the device.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            command = command_input.get("command")
            is_config = command_input.get("is_config", False)

            if command is None:
                raise HTTPException(
                    status_code=400, detail="Missing 'command' field in request body"
                )

            if is_config:
                # Execute configuration commands
                commands = command if isinstance(command, list) else [command]
                output = handler.send_config_set(commands)
            else:
                # Execute regular commands
                command_str = (
                    "\n".join(command) if isinstance(command, list) else command
                )
                output = handler.send_command(command_str)

            # Try to parse the output, but return raw output if parsing fails or returns empty result
            try:
                parsed_output = handler.parse_cli_output(
                    command_str if not is_config else "config", output
                )
                # If parsing returns an empty list/dict, return raw output instead
                if not parsed_output:
                    return {"output": output}
                return {"output": parsed_output}
            except Exception:
                # If parsing fails with an exception, return the raw output
                return {"output": output}
    except FutureTimeoutError:
        error_msg = f"Timeout executing command for device {device_id}"
        print(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Failed to execute command for device {device_id}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

