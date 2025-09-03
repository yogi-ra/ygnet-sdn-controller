from typing import List, Tuple

from .base import BaseDevice


class CiscoIosDevice(BaseDevice):
    """
    Base handler for Cisco IOS devices.
    """

    @property
    def netmiko_device_type(self) -> str:
        return "cisco_ios"

    def __init__(self, device_info):
        super().__init__(device_info)

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


class CiscoIosSwitch(CiscoIosDevice):
    """Handler for Cisco IOS Switch devices."""

    def __init__(self, device_info):
        super().__init__(device_info)