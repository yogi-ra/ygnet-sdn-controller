"""
Custom exceptions for the SDN controller project.
"""

class DeviceError(Exception):
    """Base exception class for all device-related errors."""
    pass

class DeviceConnectionError(DeviceError):
    """Raised when a connection to the device cannot be established."""
    pass

class DeviceAuthenticationError(DeviceError):
    """Raised for authentication failures."""
    pass

class DeviceTimeoutError(DeviceError):
    """Raised when a connection attempt times out."""
    pass
