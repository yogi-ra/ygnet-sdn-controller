from src.controllers.base import BaseDevice
from src.feature_schemas import FeatureSchema, FeatureType
from typing import List

# Import feature modules
from src.controllers.features.system.ubiquiti_edgeswitch import UbiquitiEdgeSwitchSystem
from src.controllers.features.interfaces.ubiquiti_edgeswitch import UbiquitiEdgeSwitchInterfaces
from src.controllers.features.vlans.ubiquiti_edgeswitch import UbiquitiEdgeSwitchVlans


class UbiquitiEdge(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        # Initialize feature modules specific to Ubiquiti EdgeSwitch
        self.system = UbiquitiEdgeSwitchSystem(self)
        self.interfaces = UbiquitiEdgeSwitchInterfaces(self)
        self.vlans = UbiquitiEdgeSwitchVlans(self)

    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_edge"

    def get_supported_features(self) -> List[FeatureSchema]:
        """
        Defines the features supported by Ubiquiti EdgeSwitch devices.
        """
        features = [
            # System Information Display
            FeatureSchema(
                name="system_info_display",
                label="System Information",
                description="Displays basic system information for the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="system.get_version_info",
                group="System",
                order=10
            ),
            # Hostname Display
            FeatureSchema(
                name="hostname_display",
                label="Hostname",
                description="Displays the hostname of the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="system.get_hostname",
                group="System",
                order=20
            ),
            # Uptime Display
            FeatureSchema(
                name="uptime_display",
                label="Uptime",
                description="Displays the uptime of the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="system.get_uptime",
                group="System",
                order=30
            ),
            # Interface Status Table
            FeatureSchema(
                name="interfaces_status_table",
                label="Interface Status",
                description="Displays the status of all interfaces on the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TABLE,
                read_only=True,
                backend_method="interfaces.get_interfaces_status",
                group="Interfaces",
                order=10
            ),
            # VLAN Brief Table
            FeatureSchema(
                name="vlan_brief_table",
                label="VLAN Brief",
                description="Displays a brief overview of VLANs configured on the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TABLE,
                read_only=True,
                backend_method="vlans.get_vlan_brief",
                group="VLANs",
                order=10
            ),
            # VLAN Details Table
            FeatureSchema(
                name="vlan_detail_table",
                label="VLAN Details",
                description="Displays detailed information about VLANs configured on the Ubiquiti EdgeSwitch device.",
                type=FeatureType.DISPLAY_TABLE,
                read_only=True,
                backend_method="vlans.get_vlan_detail",
                group="VLANs",
                order=20
            ),
            # Interface Configuration
            FeatureSchema(
                name="interface_config",
                label="Interface Configuration",
                description="Configure interface settings on the Ubiquiti EdgeSwitch device.",
                type=FeatureType.INPUT_TEXT,
                read_only=False,
                backend_method="interfaces.configure_interface",
                group="Interfaces",
                order=20,
                placeholder="Enter interface configuration commands (one per line)"
            ),
            # VLAN Creation
            FeatureSchema(
                name="vlan_create",
                label="Create VLAN",
                description="Create a new VLAN on the Ubiquiti EdgeSwitch device.",
                type=FeatureType.INPUT_TEXT,
                read_only=False,
                backend_method="vlans.create_vlan",
                group="VLANs",
                order=30,
                placeholder="Enter VLAN ID and optional name (format: ID,Name)"
            ),
            # VLAN Deletion
            FeatureSchema(
                name="vlan_delete",
                label="Delete VLAN",
                description="Delete an existing VLAN from the Ubiquiti EdgeSwitch device.",
                type=FeatureType.INPUT_TEXT,
                read_only=False,
                backend_method="vlans.delete_vlan",
                group="VLANs",
                order=40,
                placeholder="Enter VLAN ID to delete"
            ),
            # Port Security Configuration
            FeatureSchema(
                name="port_security_config",
                label="Port Security Configuration",
                description="Configure port security settings on an interface of the Ubiquiti EdgeSwitch device.",
                type=FeatureType.INPUT_TEXT,
                read_only=False,
                backend_method="interfaces.configure_port_security",
                group="Security",
                order=10,
                placeholder="Enter interface name, max MAC addresses, and violation action (format: interface,max_macs,action)"
            ),
        ]
        return features

    # Implement Ubiquiti EdgeSwitch specific methods here
    # For example, methods to handle specific CLI commands or API interactions

class UbiquitiEdgeRouter(UbiquitiEdge):
    """Handler for Ubiquiti Edge Router devices."""

    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_edgerouter"

    def __init__(self, device_info):
        super().__init__(device_info)

class UbiquitiEdgeSwitch(UbiquitiEdge):
    """Handler for Ubiquiti Edge Switch devices."""

    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_edgeswitch"

    def __init__(self, device_info):
        super().__init__(device_info)


