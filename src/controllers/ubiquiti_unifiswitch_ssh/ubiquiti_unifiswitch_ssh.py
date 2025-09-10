from typing import List
from ..base import BaseDevice
from ...device_info import DeviceConnectionInfo

class UbiquitiUnifiSwitchSSHController(BaseDevice):
    """Controller for Ubiquiti UniFi Switch devices via SSH."""
    
    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_edgeswitch"
    
    def __init__(self, device_info: DeviceConnectionInfo):
        super().__init__(device_info)
        # Initialize feature modules specific to Ubiquiti UniFi Switch
        # Currently no specific feature modules are implemented
    
    @classmethod
    def get_supported_features(cls) -> List[str]:
        """
        Defines the features supported by Ubiquiti UniFi Switch devices.
        This is a simplified version that returns feature names only.
        """
        features = [
            # Currently no specific features are implemented
        ]
        return features