from typing import List, Tuple
from .ubiquiti_edge import UbiquitiEdgeController


class UbiquitiEdgeDeviceHandler:
    """
    Handler class for Ubiquiti Edge devices.
    """
    
    def __init__(self, device_info):
        self._handler = UbiquitiEdgeController(device_info)
            
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
        Returns lists of supported view and action features for Ubiquiti Edge devices.
        """
        # For now, return the features from the base UbiquitiEdgeController class
        # In the future, this could be expanded to return device-specific features
        features = UbiquitiEdgeController.get_supported_features()
        return features, []  # No action features for now