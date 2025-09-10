from typing import List, Tuple
from .cisco_ios import CiscoIosRouter, CiscoIosSwitch


class CiscoIosDeviceHandler:
    """
    Handler class for Cisco IOS devices that delegates to the appropriate
    device-specific class based on device type.
    """
    
    def __init__(self, device_info):
        # Determine if this is a router or switch based on device type
        if device_info.device_type == "cisco_ios_router":
            self._handler = CiscoIosRouter(device_info)
        elif device_info.device_type == "cisco_ios_switch":
            self._handler = CiscoIosSwitch(device_info)
        else:
            raise ValueError(f"Unsupported Cisco IOS device type: {device_info.device_type}")
            
    def __getattr__(self, name):
        # Delegate all attribute access to the underlying handler
        return getattr(self._handler, name)
        
    def __enter__(self):
        # Delegate context manager entry to the underlying handler
        if hasattr(self._handler, '__enter__'):
            self._handler.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Delegate context manager exit to the underlying handler
        if hasattr(self._handler, '__exit__'):
            return self._handler.__exit__(exc_type, exc_val, exc_tb)
        
    @classmethod
    def get_supported_features(cls) -> Tuple[List[str], List[str]]:
        """
        Returns lists of supported view and action features for Cisco IOS devices.
        This is a simplified version that returns feature names only.
        """
        # Combine features from both router and switch
        router_view_features, router_action_features = CiscoIosRouter.get_supported_features()
        switch_view_features, switch_action_features = CiscoIosSwitch.get_supported_features()
        
        # Merge and deduplicate features
        view_features = list(set(router_view_features + switch_view_features))
        action_features = list(set(router_action_features + switch_action_features))
        
        return view_features, action_features