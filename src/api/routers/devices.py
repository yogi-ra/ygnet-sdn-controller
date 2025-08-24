from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Any, Annotated, Union, Dict
from datetime import datetime
import json

from ... import crud, schemas
from ...database import get_db
from ...cache import get_redis_client

from ...controllers import (
    get_device_handler,
    DeviceConnectionInfo,
    DEVICE_HANDLER_MAP,
)
from ..dependencies import (
    require_read_privileges,
    require_write_privileges,
    get_method_compatible_handler,
)
from ..utils import get_handler_from_device_id

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


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
    Retrieve all network devices from the database.
    """
    devices = crud.get_devices(db, skip=skip, limit=limit)
    # Ensure that the returned devices are always serialized through the schema
    return [schemas.Device.from_orm(device) for device in devices]


@router.get(
    "/{device_id}",
    response_model=schemas.DeviceDetail,
    dependencies=[Depends(require_read_privileges)],
)
def read_device(
    device_id: int,
    db: Session = Depends(get_db),
    redis_client: Any = Depends(get_redis_client),
):
    """
    Retrieve a single network device by its ID with detailed information, utilizing Redis cache.
    """
    CACHE_TTL = 300  # Cache for 5 minutes
    cache_key = f"device:{device_id}:details"

    # Try to retrieve from cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        try:
            device_detail_dict = json.loads(cached_data)
            return schemas.DeviceDetail(**device_detail_dict)
        except json.JSONDecodeError:
            # If cached data is corrupted, delete it and proceed to fetch
            redis_client.delete(cache_key)

    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    handler = get_handler_from_device_id(device_id, db)
    version_info = None
    interfaces_brief = None

    try:
        with handler:
            version_info = handler.get_version_info()
            interfaces_brief = handler.get_interfaces_brief()
    except Exception as e:
        print(f"Error fetching operational data for device {device_id}: {e}")

    device_detail = schemas.DeviceDetail(
        **db_device.__dict__,
        version=str(version_info) if version_info else None,
        interfaces=interfaces_brief if interfaces_brief else [],
    )

    # Cache the fetched data
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(device_detail.model_dump()))

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
    redis_client.delete(f"device:{device_id}:details")  # Invalidate cache
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
    redis_client.delete(f"device:{device_id}:details")  # Invalidate cache
    return


@router.get(
    "/{device_id}/version",
    response_model=Union[dict, str],
    dependencies=[Depends(require_read_privileges)],
)
def get_version(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_version_info"))],
    redis_client: Any = Depends(get_redis_client),
):
    """
    Connects to a device and retrieves its version information, utilizing Redis cache.
    """
    CACHE_TTL = 300  # Cache for 5 minutes
    cache_key = f"device:{device_id}:version"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except json.JSONDecodeError:
            redis_client.delete(cache_key)

    try:
        with handler:
            version_info = handler.get_version_info()
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(version_info))
            return version_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces",
    response_model=Union[List[dict], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_interfaces(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interfaces_brief"))
    ],
    redis_client: Any = Depends(get_redis_client),
):
    """
    Connects to a device and retrieves its interface brief, utilizing Redis cache.
    """
    CACHE_TTL = 300  # Cache for 5 minutes
    cache_key = f"device:{device_id}:interfaces"

    cached_data = redis_client.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data)
        except json.JSONDecodeError:
            redis_client.delete(cache_key)

    try:
        with handler:
            interfaces_brief = handler.get_interfaces_brief()
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(interfaces_brief))
            return interfaces_brief
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/hostname",
    response_model=str,
    dependencies=[Depends(require_read_privileges)],
)
def get_hostname(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_hostname"))],
):
    """
    Connects to a device and retrieves its hostname.
    """
    try:
        with handler:
            return handler.get_hostname()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/active-users",
    response_model=Union[List[dict], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_active_users(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_active_users"))],
):
    """
    Connects to a device and retrieves a list of currently logged-in users (active sessions).
    """
    try:
        with handler:
            return handler.get_active_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/local-users",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_local_users(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_local_users"))],
):
    """
    Connects to a device and retrieves a list of locally configured users.
    """
    try:
        with handler:
            return handler.get_local_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/clock",
    response_model=datetime,
    dependencies=[Depends(require_read_privileges)],
)
def get_clock(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_clock"))],
):
    """
    Connects to a device and retrieves its current clock/time.
    """
    try:
        with handler:
            return handler.get_clock()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vlan-details",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_vlan_details(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vlan_details"))],
):
    """
    Connects to a device and retrieves detailed VLAN information.
    """
    try:
        with handler:
            return handler.get_vlan_details()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vtp-status",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_vtp_status(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vtp_status"))],
):
    """
    Connects to a device and retrieves its VTP status.
    """
    try:
        with handler:
            return handler.get_vtp_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/spanning-tree-summary",
    response_model=Union[List[dict], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_spanning_tree_summary(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_spanning_tree_summary"))
    ],
):
    """
    Connects to a device and retrieves a summary of its Spanning Tree Protocol status.
    """
    try:
        with handler:
            return handler.get_spanning_tree_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces-trunk",
    response_model=Union[List[dict], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_interfaces_trunk(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interfaces_trunk"))
    ],
):
    """
    Connects to a device and retrieves information about its trunking interfaces.
    """
    try:
        with handler:
            return handler.get_interfaces_trunk()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/{interface_name}/config",
    response_model=List[str],
    dependencies=[Depends(require_read_privileges)],
)
def get_interface_config(
    device_id: int,
    interface_name: str,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_config"))
    ],
):
    """
    Connects to a device and retrieves the configuration for a specific interface.
    """
    try:
        with handler:
            return handler.get_interface_config(interface_name=interface_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/line-config",
    response_model=List[str],
    dependencies=[Depends(require_read_privileges)],
)
def get_line_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_line_config"))],
):
    """
    Connects to a device and retrieves its line configuration.
    """
    try:
        with handler:
            return handler.get_line_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/banners",
    response_model=Union[Dict[str, str], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_banners(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_banners"))],
):
    """
    Connects to a device and retrieves its banner configuration.
    """
    try:
        with handler:
            return handler.get_banners()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/ntp-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_ntp_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_ntp_config"))],
):
    """
    Connects to a device and retrieves its NTP configuration.
    """
    try:
        with handler:
            return handler.get_ntp_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/snmp-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_snmp_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_snmp_config"))],
):
    """
    Connects to a device and retrieves its SNMP configuration.
    """
    try:
        with handler:
            return handler.get_snmp_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/logging-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_logging_config(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_logging_config"))
    ],
):
    """
    Connects to a device and retrieves its logging configuration.
    """
    try:
        with handler:
            return handler.get_logging_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/acls",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_acls(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_acls"))],
):
    """
    Connects to a device and retrieves its Access Control Lists (ACLs).
    """
    try:
        with handler:
            return handler.get_acls()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/aaa-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_aaa_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_aaa_config"))],
):
    """
    Connects to a device and retrieves its AAA configuration.
    """
    try:
        with handler:
            return handler.get_aaa_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/cdp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_cdp_neighbors(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_cdp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its CDP neighbors.
    """
    try:
        with handler:
            return handler.get_cdp_neighbors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/ospf-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_ospf_neighbors(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_ospf_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its OSPF neighbors.
    """
    try:
        with handler:
            return handler.get_ospf_neighbors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/eigrp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_eigrp_neighbors(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_eigrp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its EIGRP neighbors.
    """
    try:
        with handler:
            return handler.get_eigrp_neighbors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/routing-protocol-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_routing_protocol_config(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_routing_protocol_config"))
    ],
):
    """
    Connects to a device and retrieves its routing protocol configuration.
    """
    try:
        with handler:
            return handler.get_routing_protocol_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/nat-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_nat_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_nat_config"))],
):
    """
    Connects to a device and retrieves its NAT configuration.
    """
    try:
        with handler:
            return handler.get_nat_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vpn-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_vpn_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vpn_config"))],
):
    """
    Connects to a device and retrieves its VPN configuration.
    """
    try:
        with handler:
            return handler.get_vpn_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/lldp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_lldp_neighbors(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_lldp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its LLDP neighbors.
    """
    try:
        with handler:
            return handler.get_lldp_neighbors()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/port-security",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_port_security(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_port_security"))
    ],
):
    """
    Connects to a device and retrieves its port security configuration.
    """
    try:
        with handler:
            return handler.get_port_security()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/etherchannel-summary",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_etherchannel_summary(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_etherchannel_summary"))
    ],
):
    """
    Connects to a device and retrieves its EtherChannel summary.
    """
    try:
        with handler:
            return handler.get_etherchannel_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vlan-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_vlan_config(
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vlan_config"))],
):
    """
    Connects to a device and retrieves its detailed VLAN configuration.
    """
    try:
        with handler:
            return handler.get_vlan_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interface-vlan-membership",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_interface_vlan_membership(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_vlan_membership"))
    ],
):
    """
    Connects to a device and retrieves its interface VLAN membership information.
    """
    try:
        with handler:
            return handler.get_interface_vlan_membership()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/{interface_name}/trunk-config",
    response_model=Union[List[Dict[str, str]], str],
    dependencies=[Depends(require_read_privileges)],
)
def get_trunk_port_config(
    device_id: int,
    interface_name: str,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_trunk_port_config"))
    ],
):
    """
    Connects to a device and retrieves the detailed trunk port configuration for a specific interface.
    """
    try:
        with handler:
            return handler.get_trunk_port_config(interface_name=interface_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/port-security",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
def get_interface_port_security(
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_port_security"))
    ],
    interface_name: str = Query(
        ..., description="Name of the interface (e.g., 'GigabitEthernet0/1')"
    ),
):
    """
    Connects to a device and retrieves the port security configuration for a specific interface.
    """
    try:
        with handler:
            return handler.get_interface_port_security(interface_name=interface_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            # If connection is successful, it's reachable
            return True
    except Exception:
        # If any exception occurs during connection, it's not reachable
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
    Returns raw or parsed data depending on the command, along with the current device level.
    """
    handler = get_handler_from_device_id(device_id, db)
    try:
        with handler:
            if command.is_config:
                # Ensure commands is a list for send_config_set
                commands_to_send = (
                    command.command
                    if isinstance(command.command, list)
                    else [command.command]
                )
                print(f"Sending config commands: {commands_to_send}")
                raw_output = handler.connection.send_config_set(commands_to_send)
                print(f"Raw output from config commands: {raw_output}")
                # For config commands, we generally don't parse the output
                # and the prompt might change to config mode.
                current_prompt = handler.connection.find_prompt()
                return {"output": raw_output, "device_level": current_prompt}
            else:
                # Use send_command for other commands
                # Ensure command is a string for send_command
                command_to_send = (
                    command.command[0]
                    if isinstance(command.command, list)
                    else command.command
                )
                print(f"Sending command: {command_to_send}")
                raw_output = handler.send_command(command_to_send)
                print(f"Raw output from command: {raw_output}")
                current_prompt = handler.connection.find_prompt()

                # Try to parse for non-config commands, if it fails, send raw.
                try:
                    parsed_output = handler.parse_cli_output(
                        command_to_send, raw_output
                    )
                    if isinstance(parsed_output, (dict, list)):
                        return {
                            "output": json.dumps(parsed_output, indent=2),
                            "device_level": current_prompt,
                        }
                    return {"output": parsed_output, "device_level": current_prompt}
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
