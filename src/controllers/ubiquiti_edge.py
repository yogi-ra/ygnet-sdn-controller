from src.controllers.base import BaseDevice
from src.feature_schemas import FeatureSchema, FeatureType
from typing import List

class UbiquitiEdge(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        # Initialize feature modules specific to Ubiquiti UniFi
        # self.system = UbiquitiUniFiSystem(self)
        # self.interfaces = UbiquitiUniFiInterfaces(self)
        # ... other feature modules

    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_edge"

    def get_supported_features(self) -> List[FeatureSchema]:
        """
        Defines the features supported by Ubiquiti UniFi devices.
        """
        features = [
            # Example: System Information Display
            FeatureSchema(
                name="system_info_display",
                label="System Information",
                description="Displays basic system information for the Ubiquiti UniFi device.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="system.get_system_info", # Placeholder for a method in a system feature module
                group="System",
                order=10
            ),
            # Add more Ubiquiti UniFi specific features here
        ]
        return features

    # Implement Ubiquiti UniFi specific methods here
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


