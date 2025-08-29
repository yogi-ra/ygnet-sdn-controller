"""
Test that the controller mapping includes the new Ubiquiti UniFi Switch device type.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_controller_mapping_includes_unifi_switch():
    """Test that the controller mapping includes the new device type."""
    from src.controllers import DEVICE_HANDLER_MAP
    from src.controllers.ubiquiti_unifi import UbiquitiUnifiSwitch
    
    # Verify that ubiquiti_unifiswitch is in the DEVICE_HANDLER_MAP
    assert "ubiquiti_unifiswitch" in DEVICE_HANDLER_MAP
    assert DEVICE_HANDLER_MAP["ubiquiti_unifiswitch"] == UbiquitiUnifiSwitch
    
    # Print all device types for verification
    print("Available device types in controller mapping:")
    for device_type, handler_class in DEVICE_HANDLER_MAP.items():
        print(f"  {device_type}: {handler_class.__name__}")

if __name__ == "__main__":
    test_controller_mapping_includes_unifi_switch()
    print("Test passed!")