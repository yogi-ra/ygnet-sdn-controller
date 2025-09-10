from typing import Union
from .cisco_ios import CiscoIosDeviceHandler
from .aruba_procurve import ArubaProcurveDeviceHandler
from .ubiquiti_edge import UbiquitiEdgeDeviceHandler
from .ubiquiti_unifiswitch_ssh import UbiquitiUnifiSwitchSSHDeviceHandler
from ..device_info import DeviceConnectionInfo
from ..exceptions import UnsupportedDeviceTypeError

# Map device type strings to their handler classes
DEVICE_HANDLER_MAP = {
    "cisco_ios_router": CiscoIosDeviceHandler,
    "cisco_ios_switch": CiscoIosDeviceHandler,
    "aruba_procurve": ArubaProcurveDeviceHandler,
    "ubiquiti_edgerouter": UbiquitiEdgeDeviceHandler,
    "ubiquiti_edgeswitch": UbiquitiEdgeDeviceHandler,
    "ubiquiti_unifiswitch": UbiquitiUnifiSwitchSSHDeviceHandler,
}

def get_device_handler(device_info: DeviceConnectionInfo) -> Union[
    CiscoIosDeviceHandler,
    ArubaProcurveDeviceHandler,
    UbiquitiEdgeDeviceHandler,
    UbiquitiUnifiSwitchSSHDeviceHandler
]:
    """
    Factory function to get the appropriate device handler based on device type.
    
    Args:
        device_info: DeviceConnectionInfo object containing device details
        
    Returns:
        Appropriate device handler instance
        
    Raises:
        UnsupportedDeviceTypeError: If the device type is not supported
    """
    handler_class = DEVICE_HANDLER_MAP.get(device_info.device_type)
    
    if not handler_class:
        raise UnsupportedDeviceTypeError(f"Unsupported device type: {device_info.device_type}")
        
    return handler_class(device_info)