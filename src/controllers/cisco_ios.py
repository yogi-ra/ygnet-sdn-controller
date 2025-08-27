from src.controllers.features.cdp.cisco_ios import CiscoIosCdp
from .base import BaseDevice
from .features.system.cisco_ios import CiscoIosSystem
from .features.interfaces.cisco_ios import CiscoIosInterfaces
from .features.vlans.cisco_ios import CiscoIosVlans
from .features.routing.cisco_ios import CiscoIosRouting
from .features.acls.cisco_ios import CiscoIosAcls
from .features.snmp.cisco_ios import CiscoIosSnmp
from .features.logging.cisco_ios import CiscoIosLogging
from .features.ntp.cisco_ios import CiscoIosNtp
from .features.aaa.cisco_ios import CiscoIosAaa


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
        self.cdp = CiscoIosCdp(self)


class CiscoIosRouter(CiscoIosDevice):
    """Handler for Cisco IOS Router devices."""

    def __init__(self, device_info):
        super().__init__(device_info)


class CiscoIosSwitch(CiscoIosDevice):
    """Handler for Cisco IOS Switch devices."""

    def __init__(self, device_info):
        super().__init__(device_info)
