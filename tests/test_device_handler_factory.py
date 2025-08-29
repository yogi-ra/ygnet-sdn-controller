import pytest
from src.controllers import get_device_handler, DEVICE_HANDLER_MAP
from src.device_info import DeviceConnectionInfo
from src.controllers.ubiquiti_unifi import UbiquitiUnifiSwitch


def test_device_handler_map_includes_unifi_switch():
    """Test that DEVICE_HANDLER_MAP includes the Ubiquiti UniFi switch."""
    assert "ubiquiti_unifiswitch" in DEVICE_HANDLER_MAP
    assert DEVICE_HANDLER_MAP["ubiquiti_unifiswitch"] == UbiquitiUnifiSwitch


def test_get_device_handler_returns_unifi_switch():
    """Test that get_device_handler returns the correct class for Ubiquiti UniFi switch."""
    device_info = DeviceConnectionInfo(
        ip_address="192.168.1.1",
        device_type="ubiquiti_unifiswitch",
        username="admin",
        password="password",
        port=22,
        name="unifi-switch"
    )
    
    handler = get_device_handler(device_info)
    
    assert isinstance(handler, UbiquitiUnifiSwitch)
    assert handler.netmiko_device_type == "ubiquiti_unifiswitch"


if __name__ == "__main__":
    pytest.main([__file__])