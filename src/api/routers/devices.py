from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
from ..decorators import cache_response

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
            return json.loads(cached_data)
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
    redis_client.setex(cache_key, CACHE_TTL, device_detail.model_dump_json())

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
    "/{device_id}/version",
    response_model=dict,
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:version", ttl=300)
def get_version(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_version_info"))],
):
    """
    Connects to a device and retrieves its version information, utilizing Redis cache.
    """
    try:
        with handler:
            version_info = handler.get_version_info()
            return version_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:interfaces", ttl=300)
def get_interfaces(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interfaces_brief"))
    ],
):
    """
    Connects to a device and retrieves its interface brief, utilizing Redis cache.
    """
    try:
        with handler:
            interfaces_brief = handler.get_interfaces_brief()
            return interfaces_brief
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/hostname",
    response_model=str,
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:hostname", ttl=300)
def get_hostname(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_hostname"))],
):
    """
    Connects to a device and retrieves its hostname, utilizing Redis cache.
    """
    try:
        with handler:
            hostname = handler.get_hostname()
            return hostname
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/active-users",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:active_users", ttl=300)
def get_active_users(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_active_users"))],
):
    """
    Connects to a device and retrieves a list of currently logged-in users (active sessions), utilizing Redis cache.
    """
    try:
        with handler:
            active_users = handler.get_active_users()
            return active_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/local-users",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:local_users", ttl=300)
def get_local_users(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_local_users"))],
):
    """
    Connects to a device and retrieves a list of locally configured users, utilizing Redis cache.
    """
    try:
        with handler:
            local_users = handler.get_local_users()
            return local_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/clock",
    response_model=datetime,
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:clock", ttl=300)
def get_clock(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_clock"))],
):
    """
    Connects to a device and retrieves its current clock/time, utilizing Redis cache.
    """
    try:
        with handler:
            clock = handler.get_clock()
            return clock
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vlan-details",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:vlan_details", ttl=300)
def get_vlan_details(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vlan_details"))],
):
    """
    Connects to a device and retrieves detailed VLAN information, utilizing Redis cache.
    """
    try:
        with handler:
            vlan_details = handler.get_vlan_details()
            return vlan_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vtp-status",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:vtp_status", ttl=300)
def get_vtp_status(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vtp_status"))],
):
    """
    Connects to a device and retrieves its VTP status, utilizing Redis cache.
    """
    try:
        with handler:
            vtp_status = handler.get_vtp_status()
            return vtp_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/spanning-tree-summary",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:spanning_tree_summary", ttl=300)
def get_spanning_tree_summary(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_spanning_tree_summary"))
    ],
):
    """
    Connects to a device and retrieves a summary of its Spanning Tree Protocol status, utilizing Redis cache.
    """
    try:
        with handler:
            spanning_tree_summary = handler.get_spanning_tree_summary()
            return spanning_tree_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces-trunk",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:interfaces_trunk", ttl=300)
def get_interfaces_trunk(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interfaces_trunk"))
    ],
):
    """
    Connects to a device and retrieves information about its trunking interfaces, utilizing Redis cache.
    """
    try:
        with handler:
            interfaces_trunk = handler.get_interfaces_trunk()
            return interfaces_trunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/{interface_name}/config",
    response_model=List[str],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:interface_config", ttl=300)
def get_interface_config(
    request: Request,
    device_id: int,
    interface_name: str,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_config"))
    ],
):
    """
    Connects to a device and retrieves the configuration for a specific interface, utilizing Redis cache.
    """
    try:
        with handler:
            interface_config = handler.get_interface_config(interface_name=interface_name)
            return interface_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/line-config",
    response_model=List[str],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:line_config", ttl=300)
def get_line_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_line_config"))],
):
    """
    Connects to a device and retrieves its line configuration, utilizing Redis cache.
    """
    try:
        with handler:
            line_config = handler.get_line_config()
            return line_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/banners",
    response_model=Dict[str, str],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:banners", ttl=300)
def get_banners(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_banners"))],
):
    """
    Connects to a device and retrieves its banner configuration, utilizing Redis cache.
    """
    try:
        with handler:
            banners = handler.get_banners()
            return banners
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/ntp-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:ntp_config", ttl=300)
def get_ntp_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_ntp_config"))],
):
    """
    Connects to a device and retrieves its NTP configuration, utilizing Redis cache.
    """
    try:
        with handler:
            ntp_config = handler.get_ntp_config()
            return ntp_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/snmp-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:snmp_config", ttl=300)
def get_snmp_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_snmp_config"))],
):
    """
    Connects to a device and retrieves its SNMP configuration, utilizing Redis cache.
    """
    try:
        with handler:
            snmp_config = handler.get_snmp_config()
            return snmp_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/logging-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:logging_config", ttl=300)
def get_logging_config(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_logging_config"))
    ],
):
    """
    Connects to a device and retrieves its logging configuration, utilizing Redis cache.
    """
    try:
        with handler:
            logging_config = handler.get_logging_config()
            return logging_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/acls",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:acls", ttl=300)
def get_acls(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_acls"))],
):
    """
    Connects to a device and retrieves its Access Control Lists (ACLs), utilizing Redis cache.
    """
    try:
        with handler:
            acls = handler.get_acls()
            return acls
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/aaa-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:aaa_config", ttl=300)
def get_aaa_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_aaa_config"))],
):
    """
    Connects to a device and retrieves its AAA configuration, utilizing Redis cache.
    """
    try:
        with handler:
            aaa_config = handler.get_aaa_config()
            return aaa_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/cdp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:cdp_neighbors", ttl=300)
def get_cdp_neighbors(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_cdp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its CDP neighbors, utilizing Redis cache.
    """
    try:
        with handler:
            cdp_neighbors = handler.get_cdp_neighbors()
            return cdp_neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/ospf-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:ospf_neighbors", ttl=300)
def get_ospf_neighbors(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_ospf_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its OSPF neighbors, utilizing Redis cache.
    """
    try:
        with handler:
            ospf_neighbors = handler.get_ospf_neighbors()
            return ospf_neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/eigrp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:eigrp_neighbors", ttl=300)
def get_eigrp_neighbors(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_eigrp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its EIGRP neighbors, utilizing Redis cache.
    """
    try:
        with handler:
            eigrp_neighbors = handler.get_eigrp_neighbors()
            return eigrp_neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/routing-protocol-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:routing_protocol_config", ttl=300)
def get_routing_protocol_config(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_routing_protocol_config"))
    ],
):
    """
    Connects to a device and retrieves its routing protocol configuration, utilizing Redis cache.
    """
    try:
        with handler:
            routing_protocol_config = handler.get_routing_protocol_config()
            return routing_protocol_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/nat-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:nat_config", ttl=300)
def get_nat_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_nat_config"))],
):
    """
    Connects to a device and retrieves its NAT configuration, utilizing Redis cache.
    """
    try:
        with handler:
            nat_config = handler.get_nat_config()
            return nat_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vpn-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:vpn_config", ttl=300)
def get_vpn_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vpn_config"))],
):
    """
    Connects to a device and retrieves its VPN configuration, utilizing Redis cache.
    """
    try:
        with handler:
            vpn_config = handler.get_vpn_config()
            return vpn_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/lldp-neighbors",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:lldp_neighbors", ttl=300)
def get_lldp_neighbors(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_lldp_neighbors"))
    ],
):
    """
    Connects to a device and retrieves its LLDP neighbors, utilizing Redis cache.
    """
    try:
        with handler:
            lldp_neighbors = handler.get_lldp_neighbors()
            return lldp_neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/port-security",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:port_security", ttl=300)
def get_port_security(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_port_security"))
    ],
):
    """
    Connects to a device and retrieves its port security configuration, utilizing Redis cache.
    """
    try:
        with handler:
            port_security = handler.get_port_security()
            return port_security
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/etherchannel-summary",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:etherchannel_summary", ttl=300)
def get_etherchannel_summary(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_etherchannel_summary"))
    ],
):
    """
    Connects to a device and retrieves its EtherChannel summary, utilizing Redis cache.
    """
    try:
        with handler:
            etherchannel_summary = handler.get_etherchannel_summary()
            return etherchannel_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/vlan-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:vlan_config", ttl=300)
def get_vlan_config(
    request: Request,
    device_id: int,
    handler: Annotated[Any, Depends(get_method_compatible_handler("get_vlan_config"))],
):
    """
    Connects to a device and retrieves its detailed VLAN configuration, utilizing Redis cache.
    """
    try:
        with handler:
            vlan_config = handler.get_vlan_config()
            return vlan_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interface-vlan-membership",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:interface_vlan_membership", ttl=300)
def get_interface_vlan_membership(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_vlan_membership"))
    ],
):
    """
    Connects to a device and retrieves its interface VLAN membership information, utilizing Redis cache.
    """
    try:
        with handler:
            interface_vlan_membership = handler.get_interface_vlan_membership()
            return interface_vlan_membership
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/{interface_name}/trunk-config",
    response_model=List[Dict[str, str]],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:trunk_port_config", ttl=300)
def get_trunk_port_config(
    request: Request,
    device_id: int,
    interface_name: str,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_trunk_port_config"))
    ],
):
    """
    Connects to a device and retrieves the detailed trunk port configuration for a specific interface, utilizing Redis cache.
    """
    try:
        with handler:
            trunk_port_config = handler.get_trunk_port_config(interface_name=interface_name)
            return trunk_port_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{device_id}/interfaces/port-security",
    response_model=List[dict],
    dependencies=[Depends(require_read_privileges)],
)
@cache_response(cache_key_prefix="device:interface_port_security", ttl=300)
def get_interface_port_security(
    request: Request,
    device_id: int,
    handler: Annotated[
        Any, Depends(get_method_compatible_handler("get_interface_port_security"))
    ],
    interface_name: str = Query(
        ..., description="Name of the interface (e.g., 'GigabitEthernet0/1')"
    ),
):
    """
    Connects to a device and retrieves the port security configuration for a specific interface, utilizing Redis cache.
    """
    try:
        with handler:
            interface_port_security = handler.get_interface_port_security(interface_name=interface_name)
            return interface_port_security
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

                # Try to parse for non-config commands. If parsing yields an empty list, send raw.
                try:
                    parsed_output = handler.parse_cli_output(
                        command_to_send, raw_output
                    )
                    if parsed_output:  # Check if parsed_output is not empty
                        return {
                            "output": json.dumps(parsed_output, indent=2),
                            "device_level": current_prompt,
                        }
                    else: # If parsed_output is empty (no template found or no data), return raw_output
                        return {"output": raw_output, "device_level": current_prompt}
                except Exception: # If an actual exception occurs during parsing, return raw_output
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
