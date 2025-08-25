"""
This package contains device controller classes and a factory function to instantiate them.
"""
from typing import Dict, Type

from .base import BaseDevice
from .cisco_ios import CiscoIosRouter, CiscoIosSwitch, CiscoIosDevice
from ..device_info import DeviceConnectionInfo

# The map that the factory function uses to find the correct class
# Maps our internal device_type string to the corresponding handler class
DEVICE_HANDLER_MAP: Dict[str, Type[BaseDevice]] = {
    "cisco_ios_router": CiscoIosRouter,
    "cisco_ios_switch": CiscoIosSwitch,
}

def get_device_handler(device_info: DeviceConnectionInfo) -> BaseDevice:
    """
    Factory function that returns an instance of the correct device handler class.

    Args:
        device_info: The device connection information.

    Returns:
        An instance of a BaseDevice subclass.

    Raises:
        NotImplementedError: If the device_type is not supported.
    """
    handler_class = DEVICE_HANDLER_MAP.get(device_info.device_type)
    if not handler_class:
        raise NotImplementedError(f"Device type '{device_info.device_type}' is not supported.")
    
    return handler_class(device_info)

# Make the public interface cleaner
__all__ = [
    "get_device_handler",
    "DeviceConnectionInfo",
    "BaseDevice",
    "CiscoIosRouter",
    "CiscoIosSwitch",
    "CiscoIosDevice",
]