from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Any, Dict
import json
import inspect

from ...crud import crud, schemas
from ...database import get_db
from ...cache import get_redis_client
from ...controllers import DEVICE_HANDLER_MAP
from ...controllers.features.base import BaseFeature
from ...device_info import DeviceConnectionInfo
from ...feature_schemas import FeatureSchema, HeaderFieldSchema, HeaderFieldType # Added this import


from ..dependencies import (
    require_read_privileges,
    require_write_privileges,
)
from ..utils import get_handler_from_device_id
from ..decorators import cache_response

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


@router.get("/supported-features", response_model=Dict[str, List[str]], dependencies=[Depends(require_read_privileges)])
def get_supported_features():
    """
    Returns a dictionary of supported device types and their features.
    """
    supported_features = {}
    dummy_device_info = DeviceConnectionInfo(
        ip_address="dummy",
        port=22,
        device_type="dummy",
        username="dummy",
        password="dummy",
    )
    for device_type, handler_class in DEVICE_HANDLER_MAP.items():
        try:
            features_raw = handler_class.get_supported_features()
            if not isinstance(features_raw, list):
                raise TypeError(f"get_supported_features for {device_type} did not return a list: {features_raw}")
            features = [
                feature.name
                for feature in features_raw
            ]
            supported_features[device_type] = features
        except Exception as e:
            print(f"Error instantiating handler or getting supported features for device type {device_type}: {e}. features_raw: {features_raw}")
            supported_features[device_type] = []
    print(f"DEBUG: Final supported_features: {supported_features}")
    return supported_features


@router.get(
    "/{device_id}/features",
    response_model=Dict[str, Any], # Changed response_model to Dict[str, Any]
    dependencies=[Depends(require_read_privileges)],
)
async def get_device_features(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns a list of FeatureSchema objects and header fields for a specific device.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)
    
    features = []
    header_fields = []

    try:
        with handler:
            features = handler.get_supported_features()
            
            # Populate header fields
            try:
                hostname = handler.system.get_hostname()
            except Exception:
                hostname = "N/A"
            header_fields.append(HeaderFieldSchema(
                name="hostname",
                label="Hostname",
                type=HeaderFieldType.TEXT,
                value=hostname,
                order=1
            ))
            header_fields.append(HeaderFieldSchema(
                name="ip_address",
                label="IP Address",
                type=HeaderFieldType.TEXT,
                value=db_device.ip_address,
                order=2
            ))
            header_fields.append(HeaderFieldSchema(
                name="device_type",
                label="Device Type",
                type=HeaderFieldType.TEXT,
                value=db_device.device_type,
                order=3
            ))
            try:
                is_reachable = handler.check_reachability()
            except Exception:
                is_reachable = False
            header_fields.append(HeaderFieldSchema(
                name="is_reachable",
                label="Status",
                type=HeaderFieldType.STATUS,
                value=is_reachable,
                order=4
            ))
            try:
                uptime = handler.system.get_uptime()
            except Exception:
                uptime = "N/A"
            header_fields.append(HeaderFieldSchema(
                name="uptime",
                label="Uptime",
                type=HeaderFieldType.TEXT,
                value=uptime,
                order=5
            ))
            try:
                last_updated = handler.system.get_clock()
            except Exception:
                last_updated = "N/A"
            header_fields.append(HeaderFieldSchema(
                name="last_updated",
                label="Last Updated",
                type=HeaderFieldType.TEXT,
                value=last_updated,
                order=6
            ))

            # Sort header fields by order
            header_fields.sort(key=lambda x: x.order or 999)

            print(f"DEBUG: Features returned for device {device_id}: {features}")
            print(f"DEBUG: Header fields returned for device {device_id}: {header_fields}")
            
            return {"features": features, "header_fields": header_fields}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/", response_model=schemas.Device, dependencies=[Depends(require_write_privileges)]
)
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """
    Create a new network device in the database.
    """
    if crud.get_device_by_name(db, name=device.name):
        raise HTTPException(status_code=400, detail="Device name already registered")
    return crud.create_device(db=db, device=device)


@router.get(
    "/",
    response_model=List[schemas.Device],
    dependencies=[Depends(require_read_privileges)],
)
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all network devices from the database, including their reachability status.
    """
    db_devices = crud.get_devices(db, skip=skip, limit=limit)
    devices_with_status = []
    for db_device in db_devices:
        device_dict = schemas.Device.from_orm(db_device).dict()
        try:
            handler = get_handler_from_device_id(db_device.id, db)
            device_dict["is_reachable"] = handler.check_reachability()
        except Exception as e:
            device_dict["is_reachable"] = False
            print(f"Error checking reachability for device {db_device.id}: {e}")
        devices_with_status.append(device_dict)
    return devices_with_status


@router.get(
    "/{device_id}",
    response_model=schemas.DeviceDetail,
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:details", ttl=300)
def read_device(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single network device by its ID with detailed information, utilizing Redis cache.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)
    version_info = None
    interfaces_brief = None

    try:
        with handler:
            raw_version_info = handler.system.get_version_info()
            version_info = raw_version_info[0] if raw_version_info else None
            interfaces_brief = handler.interfaces.get_interfaces_brief()
    except Exception as e:
        print(f"Error fetching operational data for device {device_id}: {e}")

    device_detail = schemas.DeviceDetail(
        **db_device.__dict__,
        version=version_info if version_info else None,
        interfaces=interfaces_brief if interfaces_brief else [],
    )

    return device_detail


@router.put(
    "/{device_id}",
    response_model=schemas.Device,
    dependencies=[Depends(require_write_privileges)],
)
def update_device(
    device_id: int,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
):
    """
    Update an existing network device in the database and invalidate cache.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    updated_device = crud.update_device(
        db, device_id=device_id, device_update=device_update
    )
    # Invalidate all caches related to this device
    for key in redis_client.scan_iter(f"device:{device_id}:*"):
        redis_client.delete(key)
    return updated_device


@router.delete(
    "/{device_id}", status_code=204, dependencies=[Depends(require_write_privileges)]
)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
):
    """
    Delete a network device from the database and invalidate cache.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    crud.delete_device(db, device_id=device_id)
    # Invalidate all caches related to this device
    for key in redis_client.scan_iter(f"device:{device_id}:*"):
        redis_client.delete(key)
    return


@router.get(
    "/{device_id}/features/{feature_name}",
    response_model=Any,
    dependencies=[Depends(require_read_privileges)],
)
async def get_feature(
    request: Request,
    device_id: int,
    feature_name: str,
    db: Session = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
):
    """
    Retrieves feature data from a device, using a cache-aside pattern with Redis.
    The data is stored in Redis as a JSON string.
    """
    cache_key = f"device:{device_id}:features:{feature_name}"
    cached_data = redis_client.get(cache_key)

    if cached_data:
        return json.loads(cached_data)

    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            supported_features = handler.get_supported_features()
            feature_schema = next(
                (f for f in supported_features if f.name == feature_name),
                None,
            )

            if not feature_schema:
                raise HTTPException(
                    status_code=404, detail=f"Feature '{feature_name}' not found for this device."
                )

            if not feature_schema.backend_method:
                raise HTTPException(
                    status_code=400, detail=f"Feature '{feature_name}' does not have a backend method defined."
                )

            # Dynamically call the backend method
            # backend_method is in the format "sub_object.method_name"
            parts = feature_schema.backend_method.split('.')
            if len(parts) != 2:
                raise HTTPException(
                    status_code=500, detail=f"Invalid backend_method format: {feature_schema.backend_method}"
                )
            
            sub_object_name, method_name = parts

            # Get the feature object (e.g., handler.system, handler.aaa)
            feature_obj = getattr(handler, sub_object_name, None)
            if feature_obj is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Feature '{feature_name}' not available for this device type.",
                )

            # Get the method for the feature
            feature_method = getattr(feature_obj, method_name, None)

            if feature_method is None or not callable(feature_method):
                raise HTTPException(
                    status_code=404,
                    detail=f"Method '{method_name}' not found or not callable for feature '{feature_name}'.",
                )

            data = feature_method()
            redis_client.set(cache_key, json.dumps(data), ex=300)
            return data
    except NotImplementedError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Feature method not implemented for this device type: {e}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{device_id}/action",
    status_code=200,
    dependencies=[Depends(require_write_privileges)],
)
async def perform_feature_action(
    device_id: int,
    action_request: schemas.FeatureActionRequest,
    db: Session = Depends(get_db),
):
    """
    Performs an action on a specific device feature.
    """
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)

    # Find the FeatureSchema for the requested feature_name
    supported_features = handler.get_supported_features()
    feature_schema = next(
        (f for f in supported_features if f.name == action_request.feature_name),
        None,
    )

    if not feature_schema:
        raise HTTPException(
            status_code=404, detail=f"Feature '{action_request.feature_name}' not found for this device."
        )

    if not feature_schema.backend_method:
        raise HTTPException(
            status_code=400, detail=f"Feature '{action_request.feature_name}' does not have a backend method defined."
        )

    try:
        with handler:
            # Dynamically call the backend method
            # backend_method is in the format "sub_object.method_name"
            parts = feature_schema.backend_method.split('.')
            if len(parts) != 2:
                raise HTTPException(
                    status_code=500, detail=f"Invalid backend_method format: {feature_schema.backend_method}"
                )
            
            sub_object_name, method_name = parts
            
            feature_obj = getattr(handler, sub_object_name, None)
            if feature_obj is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sub-object '{sub_object_name}' not found on device handler.",
                )
            
            method_to_call = getattr(feature_obj, method_name, None)
            if method_to_call is None or not callable(method_to_call):
                raise HTTPException(
                    status_code=404,
                    detail=f"Method '{method_name}' not found or not callable on sub-object '{sub_object_name}'.",
                )
            
            # Execute the method with the provided value
            result = method_to_call(action_request.value)
            return {"message": "Action performed successfully", "result": result}

    except NotImplementedError as e:
        raise HTTPException(
            status_code=400, detail=f"Feature action not implemented for this device type: {e}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{device_id}/cache/clear",
    status_code=204,
    dependencies=[Depends(require_write_privileges)],
)
def clear_cache(
    device_id: int,
    cache_clear_input: schemas.CacheClearInput,
    redis_client: Any = Depends(get_redis_client),
):
    """
    Invalidates the cache for specific feature(s) of a device.
    """
    cleared_keys = []
    # Use a more generic scan to clear all keys related to the device_id
    # This pattern matches keys like "device:details:{device_id}", "device:{device_id}:features:{feature_name}", etc.
    for key in redis_client.scan_iter(f"device:{device_id}:*"):
        redis_client.delete(key)
        cleared_keys.append(key)

    # Also clear the specific device details cache if it doesn't match the above pattern exactly
    # (e.g., if it was just "device:details" without the device_id in the prefix)
    detail_key = f"device:details:{device_id}"
    if redis_client.exists(detail_key):
        redis_client.delete(detail_key)
        cleared_keys.append(detail_key)

    return


@router.get(
    "/{device_id}/check-reachability",
    response_model=bool,
    dependencies=[Depends(require_read_privileges)],
)
def check_device_reachability(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    Checks if a device is reachable by attempting to establish a Netmiko connection.
    """
    try:
        handler = get_handler_from_device_id(device_id, db)
        with handler:
            return True
    except Exception:
        return False


@router.post(
    "/{device_id}/execute-command",
    response_model=schemas.SingleCommandOutput,
    dependencies=[Depends(require_write_privileges)],
)
def run_command(
    device_id: int, command: schemas.CommandInput, db: Session = Depends(get_db)
):
    """
    Connects to a device and runs an arbitrary command.
    Returns raw or parsed data depending on the command.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            if command.is_config:
                commands_to_send = (
                    command.command
                    if isinstance(command.command, list)
                    else [command.command]
                )
                raw_output = handler.connection.send_config_set(commands_to_send)
                current_prompt = handler.connection.find_prompt()
                return {"output": raw_output, "device_level": current_prompt}
            else:
                command_to_send = (
                    command.command[0]
                    if isinstance(command.command, list)
                    else command.command
                )
                raw_output = handler.send_command(command_to_send)
                current_prompt = handler.connection.find_prompt()
                try:
                    parsed_output = handler.parse_cli_output(
                        command_to_send, raw_output
                    )
                    output = (
                        json.dumps(parsed_output, indent=2)
                        if parsed_output
                        else raw_output
                    )
                    return {"output": output, "device_level": current_prompt}
                except Exception:
                    return {"output": raw_output, "device_level": current_prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{device_id}/execute-multiline-command",
    response_model=schemas.MultilineCommandOutput,
    dependencies=[Depends(require_write_privileges)],
)
def run_multiline_command(
    device_id: int,
    multiline_command: schemas.MultilineCommandRequest,
    db: Session = Depends(get_db),
):
    """
    Connects to a device and runs multiple commands, handling additional prompts.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            output = handler.send_multiline_commands(multiline_command.commands)
            return schemas.MultilineCommandOutput(output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))