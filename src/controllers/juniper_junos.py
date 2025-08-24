from .base import BaseDevice

class JuniperJunosDevice(BaseDevice):
    """Handler for Juniper Junos devices."""
    @property
    def netmiko_device_type(self) -> str:
        """
        Returns the Netmiko device_type string for Juniper JUNOS devices.
        """
        return "juniper_junos"
