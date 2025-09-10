from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Union
from concurrent.futures import TimeoutError as FutureTimeoutError
from ....crud import crud
from ....database import get_db
from ....cache import get_redis_client
from ....exceptions import DeviceUnreachableError, DeviceConnectionError, DeviceAuthenticationError, DeviceTimeoutError
from ...decorators import cache_response
from ...dependencies import (
    require_read_privileges,
    require_write_privileges,
)
from ...utils import get_handler_from_device_id

router = APIRouter(tags=["Device System"])

@router.post("/{device_id}/execute-command", dependencies=[Depends(require_write_privileges)])
def execute_command(
    device_id: int,
    command_input: Dict[str, Any],
    db: Session = Depends(get_db)
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
                raise HTTPException(status_code=400, detail="Missing 'command' field in request body")
            
            if is_config:
                # Execute configuration commands
                commands = command if isinstance(command, list) else [command]
                output = handler.send_config_set(commands)
            else:
                # Execute regular commands
                command_str = '\n'.join(command) if isinstance(command, list) else command
                output = handler.send_command(command_str)
            
            # Try to parse the output, but return raw output if parsing fails or returns empty result
            try:
                parsed_output = handler.parse_cli_output(command_str if not is_config else "config", output)
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