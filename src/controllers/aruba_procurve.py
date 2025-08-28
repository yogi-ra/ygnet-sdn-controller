from src.controllers.base import BaseDevice
from typing import List
from src.feature_schemas import FeatureSchema, FeatureType
from src.controllers.features.system.aruba_procurve import ArubaProcurveSystem

class ArubaProcurve(BaseDevice):
    @property
    def netmiko_device_type(self) -> str:
        return "hp_procurve"
    def __init__(self, device_info):
        super().__init__(device_info)
        self.system = ArubaProcurveSystem(self)

    @classmethod
    def get_supported_features(cls) -> List[FeatureSchema]:
        return [
            FeatureSchema(
                name="system_version",
                label="System Version",
                description="Displays the device's system version information.",
                type=FeatureType.DISPLAY_TEXT,
                read_only=True,
                backend_method="system.get_version_info",
                group="System",
                order=1
            ),
        ]
