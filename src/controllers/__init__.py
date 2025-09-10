"""
This package contains device controller classes and a factory function to instantiate them.
"""
from typing import Dict, Type

from .base import BaseDevice
from .device_handler_factory import get_device_handler
from ..device_info import DeviceConnectionInfo

# Make the public interface cleaner
__all__ = [
    "get_device_handler",
    "DeviceConnectionInfo",
    "BaseDevice",
]
