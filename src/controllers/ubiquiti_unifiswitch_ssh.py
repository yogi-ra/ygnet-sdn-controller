from src.controllers.base import BaseDevice
from src.feature_schemas import FeatureSchema, FeatureType
from typing import List

class UbiquitiUnifiSwitchSSH(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        # Initialize feature modules specific to Ubiquiti UniFi Switch
        # self.system = UbiquitiEdgeSwitchSystem(self)
        # self.interfaces = UbiquitiEdgeSwitchInterfaces(self)
        # self.vlans = UbiquitiEdgeSwitchVlans(self)

    @property
    def netmiko_device_type(self) -> str:
        return "ubiquiti_unifiswitch_ssh"

    def get_supported_features(self) -> List[FeatureSchema]:
        """
        Defines the features supported by Ubiquiti UniFi Switch devices.
        """
        features = [
            # # Port Security Configuration
            # FeatureSchema(
            #     name="port_security_config",
            #     label="Port Security Configuration",
            #     description="Configure port security settings on an interface of the Ubiquiti UniFi Switch device.",
            #     type=FeatureType.INPUT_TEXT,
            #     read_only=False,
            #     backend_method="interfaces.configure_port_security",
            #     group="Security",
            #     order=10,
            #     placeholder="Enter interface name, max MAC addresses, and violation action (format: interface,max_macs,action)"
            # ),
        ]
        return features
