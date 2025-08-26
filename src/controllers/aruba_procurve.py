from src.controllers.base import BaseDevice
from src.controllers.features.system.aruba_procurve import ArubaProcurveSystem

class ArubaProcurve(BaseDevice):
    def __init__(self, device_info):
        super().__init__(device_info)
        self.system = ArubaProcurveSystem(self)
