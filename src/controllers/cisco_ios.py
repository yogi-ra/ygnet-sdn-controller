from typing import List, Dict, Any, Union, Tuple

from .base import BaseDevice
from src.feature_schemas import ViewFeatureSchema, ActionFeatureSchema, ViewFeatureType, ActionFeatureType, TableAction
from .features.system.cisco_ios import CiscoIosSystem
from .features.interfaces.cisco_ios import CiscoIosInterfaces
from .features.vlans.cisco_ios import CiscoIosVlans
from .features.routing.cisco_ios import CiscoIosRouting
from .features.acls.cisco_ios import CiscoIosAcls
from .features.snmp.cisco_ios import CiscoIosSnmp
from .features.logging.cisco_ios import CiscoIosLogging
from .features.ntp.cisco_ios import CiscoIosNtp
from .features.aaa.cisco_ios import CiscoIosAaa
from .features.lldp.cisco_ios import CiscoIosLldp
from .features.arp.cisco_ios import CiscoIosArp
from .features.cdp.cisco_ios import CiscoIosCdp


class CiscoIosDevice(BaseDevice):
    """
    Base handler for Cisco IOS devices.
    This class is composed of feature-based classes.
    """

    @property
    def netmiko_device_type(self) -> str:
        return "cisco_ios"

    def __init__(self, device_info):
        super().__init__(device_info)
        self.system = CiscoIosSystem(self)
        self.interfaces = CiscoIosInterfaces(self)
        self.vlans = CiscoIosVlans(self)
        self.routing = CiscoIosRouting(self)
        self.acls = CiscoIosAcls(self)
        self.snmp = CiscoIosSnmp(self)
        self.logging = CiscoIosLogging(self)
        self.ntp = CiscoIosNtp(self)
        self.aaa = CiscoIosAaa(self)
        self.lldp = CiscoIosLldp(self)
        self.arp = CiscoIosArp(self)
        self.cdp = CiscoIosCdp(self)

    @classmethod
    def get_supported_features(cls) -> Tuple[List[ViewFeatureSchema], List[ActionFeatureSchema]]:
        view_features = [
            ViewFeatureSchema(
                name="system_version",
                label="System Version",
                description="Displays the device's system version information.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="system.get_version_info",
                group="System",
                order=1
            ),
            ViewFeatureSchema(
                name="interfaces_brief",
                label="Interfaces Brief",
                description="Displays a brief summary of all interfaces.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="interfaces.get_interfaces_brief",
                group="Interfaces",
                order=1,
                actions=[
                    TableAction(
                        feature_name="interface_toggle",
                        backend_method="interfaces.set_interface_state"
                    )
                ],
                row_identifier="interface"
            ),
            ViewFeatureSchema(
                name="aaa_config",
                label="AAA Configuration",
                description="Displays the current AAA configuration.",
                type=ViewFeatureType.DISPLAY_TEXT,
                backend_method="aaa.get_aaa_config",
                group="Security",
                order=2
            ),
            ViewFeatureSchema(
                name="ntp_config",
                label="NTP Configuration",
                description="Displays the current NTP configuration.",
                type=ViewFeatureType.DISPLAY_TEXT,
                backend_method="ntp.get_ntp_config",
                group="System",
                order=2
            ),
            ViewFeatureSchema(
                name="logging_config",
                label="Logging Configuration",
                description="Displays the current logging configuration.",
                type=ViewFeatureType.DISPLAY_TEXT,
                backend_method="logging.get_logging_config",
                group="System",
                order=3
            ),
            ViewFeatureSchema(
                name="lldp_neighbors",
                label="LLDP Neighbors",
                description="Displays LLDP neighbor information.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="lldp.get_lldp_neighbors",
                group="Discovery",
                order=1
            ),
            ViewFeatureSchema(
                name="arp_table",
                label="ARP Table",
                description="Displays the device's ARP table.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="arp.get_ip_arp",
                group="Network",
                order=1
            ),
            ViewFeatureSchema(
                name="cdp_neighbors",
                label="CDP Neighbors",
                description="Displays CDP neighbor information.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="cdp.get_cdp_neighbors",
                group="Discovery",
                order=2
            ),
            ViewFeatureSchema(
                name="vlans_brief",
                label="VLANs Brief",
                description="Displays a brief summary of all VLANs.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="vlans.get_vlan_brief",
                group="VLANs",
                order=1
            ),
            ViewFeatureSchema(
                name="routing_table",
                label="Routing Table",
                description="Displays the device's IP routing table.",
                type=ViewFeatureType.DISPLAY_TABLE,
                backend_method="routing.get_routing_table",
                group="Routing",
                order=1
            ),
            ViewFeatureSchema(
                name="acls_config",
                label="ACLs Configuration",
                description="Displays the device's Access Control Lists.",
                type=ViewFeatureType.DISPLAY_TEXT,
                backend_method="acls.get_acls",
                group="Security",
                order=3
            ),
        ]

        action_features = [
            
            ActionFeatureSchema(
                name="snmp_config",
                label="SNMP Configuration",
                description="Edit the current SNMP configuration.",
                type=ActionFeatureType.TEXT_AREA,
                backend_method="snmp.set_snmp_config",
                group="Security",
                order=1
            ),
            ActionFeatureSchema(
                name="snmp_status_toggle",
                label="Enable/Disable SNMP",
                description="Toggles SNMP service on the device.",
                type=ActionFeatureType.TOGGLE,
                backend_method="snmp.toggle_snmp_service",
                group="Security",
                order=4
            ),
            ActionFeatureSchema(
                name="ntp_server_ip",
                label="Set NTP Server IP",
                description="Configures the NTP server IP address.",
                type=ActionFeatureType.INPUT_TEXT,
                backend_method="ntp.set_ntp_server",
                placeholder="e.g., 192.168.1.1",
                validation_rules={"pattern": "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", "error_message": "Invalid IP address format."},
                group="System",
                order=4
            ),
            ActionFeatureSchema(
                name="reload_device",
                label="Reload Device",
                description="Reloads the device. Use with caution!",
                type=ActionFeatureType.BUTTON,
                backend_method="system.reload_device",
                group="System",
                order=5
            ),
        ]

        return view_features, action_features


class CiscoIosRouter(CiscoIosDevice):
    """Handler for Cisco IOS Router devices."""

    def __init__(self, device_info):
        super().__init__(device_info)


class CiscoIosSwitch(CiscoIosDevice):
    """Handler for Cisco IOS Switch devices."""

    def __init__(self, device_info):
        super().__init__(device_info)
