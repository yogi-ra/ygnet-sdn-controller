from typing import List
from ..base import BaseDevice
from ...device_info import DeviceConnectionInfo
from ..features.system.aruba_procurve import ArubaProcurveSystem

class ArubaProcurveController(BaseDevice):
    """Controller for Aruba Procurve devices."""
    
    @property
    def netmiko_device_type(self) -> str:
        return "hp_procurve"
    
    def __init__(self, device_info: DeviceConnectionInfo):
        super().__init__(device_info)
        # Initialize feature modules specific to Aruba Procurve
        self.system = ArubaProcurveSystem(self)
    
    @classmethod
    def get_supported_features(cls) -> List[str]:
        """
        Defines the features supported by Aruba Procurve devices.
        This is a simplified version that returns feature names only.
        """
        features = [
            "system_info_display",
            "system_uptime_display",
            "system_clock_display",
            "interfaces_brief_table",
            "interfaces_status_table"
        ]
        return features