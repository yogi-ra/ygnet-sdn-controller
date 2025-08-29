"""
End-to-end test for Ubiquiti UniFi switch support.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_end_to_end_unifi_switch_support():
    """Test the complete flow for Ubiquiti UniFi switch support."""
    print("Testing end-to-end Ubiquiti UniFi switch support...")
    
    # 1. Test that the DeviceType enum includes UBIQUITI_UNIFISWITCH
    from src.schemas import DeviceType
    assert hasattr(DeviceType, "UBIQUITI_UNIFISWITCH")
    assert DeviceType.UBIQUITI_UNIFISWITCH.value == "ubiquiti_unifiswitch"
    print("[OK] DeviceType enum includes UBIQUITI_UNIFISWITCH")
    
    # 2. Test that the controller module can be imported
    from src.controllers.ubiquiti_unifi import UbiquitiUnifiSwitch
    print("[OK] UbiquitiUnifiSwitch class can be imported")
    
    # 3. Test that the controller mapping includes the new device type
    from src.controllers import DEVICE_HANDLER_MAP
    assert "ubiquiti_unifiswitch" in DEVICE_HANDLER_MAP
    assert DEVICE_HANDLER_MAP["ubiquiti_unifiswitch"] == UbiquitiUnifiSwitch
    print("[OK] DEVICE_HANDLER_MAP includes ubiquiti_unifiswitch")
    
    # 4. Test that we can create an instance of the controller
    from src.device_info import DeviceConnectionInfo
    device_info = DeviceConnectionInfo(
        ip_address="192.168.1.1",
        device_type="ubiquiti_unifiswitch",
        username="admin",
        password="password",
        port=22,
        name="test-unifi-switch"
    )
    
    controller = UbiquitiUnifiSwitch(device_info)
    assert controller.netmiko_device_type == "ubiquiti_unifiswitch"
    print("[OK] UbiquitiUnifiSwitch instance created successfully")
    
    # 5. Test that the controller returns features
    features = controller.get_supported_features()
    assert isinstance(features, list)
    assert len(features) > 0
    print("[OK] Controller returns supported features")
    
    # 6. Test that the factory function returns the correct controller
    from src.controllers import get_device_handler
    handler = get_device_handler(device_info)
    assert isinstance(handler, UbiquitiUnifiSwitch)
    print("[OK] get_device_handler returns correct controller type")
    
    print("\nAll tests passed! Ubiquiti UniFi switch support is working correctly.")

if __name__ == "__main__":
    test_end_to_end_unifi_switch_support()