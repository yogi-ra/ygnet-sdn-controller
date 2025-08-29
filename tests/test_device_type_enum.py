"""
Test that the DeviceType enum includes the new Ubiquiti UniFi Switch device type.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_device_type_enum_includes_unifi_switch():
    """Test that the DeviceType enum includes the new device type."""
    from schemas import DeviceType
    
    # Verify that UBIQUITI_UNIFISWITCH is in the enum
    assert hasattr(DeviceType, "UBIQUITI_UNIFISWITCH")
    assert DeviceType.UBIQUITI_UNIFISWITCH.value == "ubiquiti_unifiswitch"
    
    # Print all device types for verification
    print("Available device types:")
    for attr in dir(DeviceType):
        if not attr.startswith('_'):
            value = getattr(DeviceType, attr)
            if hasattr(value, 'value'):
                print(f"  {attr}: {value.value}")

if __name__ == "__main__":
    test_device_type_enum_includes_unifi_switch()
    print("Test passed!")