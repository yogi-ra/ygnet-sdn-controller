from typing import List, Tuple

from ..base import BaseDevice
from .features.system.cisco_ios import CiscoIosSystem
from .features.interfaces.cisco_ios import CiscoIosInterfaces
from .features.vlans.cisco_ios import CiscoIosVlans
from .features.routing.cisco_ios import CiscoIosRouting


class CiscoIosDevice(BaseDevice):
    """
    Base handler for Cisco IOS devices.
    """

    @property
    def netmiko_device_type(self) -> str:
        return "cisco_ios"

    def __init__(self, device_info):
        super().__init__(device_info)
        # Initialize feature modules specific to Cisco IOS
        self.system = CiscoIosSystem(self)
        self.interfaces = CiscoIosInterfaces(self)
        
    @classmethod
    def get_supported_features(cls) -> Tuple[List[str], List[str]]:
        """
        Returns lists of supported view and action features for Cisco IOS devices.
        This is a simplified version that returns feature names only.
        """
        # Define basic feature names
        view_features = [
            "system_version",
            "system_hostname",
            "system_uptime",
            "system_clock",
            "interfaces_brief",
            "interfaces_status"
        ]
        
        action_features = [
            "interface_state_toggle",
            "system_reboot"
        ]
        
        return view_features, action_features


class CiscoIosRouter(CiscoIosDevice):
    """Handler for Cisco IOS Router devices."""

    def __init__(self, device_info):
        super().__init__(device_info)
        self.routing = CiscoIosRouting(self)

    @classmethod
    def get_supported_features(cls) -> Tuple[List[str], List[str]]:
        """
        Returns lists of supported view and action features for Cisco IOS Switch devices.
        This is a simplified version that returns feature names only.
        """
        # Define basic feature names
        view_features = [
            "system_version",
            "system_hostname",
            "system_uptime",
            "system_clock",
            "interfaces_brief",
            "interfaces_status",
            "routing_ip_route"
        ]
        
        action_features = [
            "interface_state_toggle",
            "system_reboot"
        ]
        
        return view_features, action_features


class CiscoIosSwitch(CiscoIosDevice):
    """Handler for Cisco IOS Switch devices."""

    def __init__(self, device_info):
        super().__init__(device_info)
        # Initialize VLAN feature for switches
        self.vlans = CiscoIosVlans(self)
        
    @classmethod
    def get_supported_features(cls) -> Tuple[List[str], List[str]]:
        """
        Returns lists of supported view and action features for Cisco IOS Switch devices.
        This is a simplified version that returns feature names only.
        """
        # Define basic feature names
        view_features = [
            "system_version",
            "system_hostname",
            "system_uptime",
            "system_clock",
            "interfaces_brief",
            "interfaces_status",
            "vlans_brief"
        ]
        
        action_features = [
            "interface_state_toggle",
            "system_reboot"
        ]
        
        return view_features, action_features