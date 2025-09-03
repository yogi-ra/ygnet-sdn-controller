from typing import List
from .base import BaseController
from ..device_info import DeviceConnectionInfo

# Import feature modules
from ..controllers.features.system.ubiquiti_edgeswitch import UbiquitiEdgeSwitchSystem
from ..controllers.features.interfaces.ubiquiti_edgeswitch import UbiquitiEdgeSwitchInterfaces
from ..controllers.features.vlans.ubiquiti_edgeswitch import UbiquitiEdgeSwitchVlans

class UbiquitiEdgeController(BaseController):
    """Controller for Ubiquiti Edge devices."""
    
    def __init__(self, device_info: DeviceConnectionInfo):
        super().__init__(device_info)
        # Initialize feature modules specific to Ubiquiti EdgeSwitch
        self.system = UbiquitiEdgeSwitchSystem(self.device_info)
        self.interfaces = UbiquitiEdgeSwitchInterfaces(self.device_info)
        self.vlans = UbiquitiEdgeSwitchVlans(self.device_info)
    
    @classmethod
    def get_supported_features(cls) -> List[str]:
        """
        Defines the features supported by Ubiquiti EdgeSwitch devices.
        This is a simplified version that returns feature names only.
        """
        features = [
            "system_info_display",
            "system_uptime_display",
            "system_clock_display",
            "interfaces_brief_table",
            "interfaces_status_table",
            "vlans_brief_table",
            "vlans_status_table",
            "hostname_input",
            "domain_name_input",
            "snmp_community_input",
            "ntp_server_input"
        ]
        return features