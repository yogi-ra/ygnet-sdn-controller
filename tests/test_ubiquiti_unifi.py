import pytest
from unittest.mock import MagicMock, patch
from src.controllers.ubiquiti_unifi import UbiquitiUnifiSwitch
from src.device_info import DeviceConnectionInfo


def test_ubiquiti_unifi_switch_initialization():
    """Test that UbiquitiUnifiSwitch initializes correctly."""
    device_info = DeviceConnectionInfo(
        ip_address="192.168.1.1",
        device_type="ubiquiti_unifiswitch",
        username="admin",
        password="password",
        port=22,
        name="unifi-switch"
    )
    
    switch = UbiquitiUnifiSwitch(device_info)
    
    # Check that the device type is set correctly
    assert switch.netmiko_device_type == "ubiquiti_unifiswitch"
    
    # Check that feature modules are initialized
    assert hasattr(switch, 'system')
    assert hasattr(switch, 'interfaces')
    assert hasattr(switch, 'vlans')


def test_ubiquiti_unifi_switch_features():
    """Test that UbiquitiUnifiSwitch returns the correct features."""
    device_info = DeviceConnectionInfo(
        ip_address="192.168.1.1",
        device_type="ubiquiti_unifiswitch",
        username="admin",
        password="password",
        port=22,
        name="unifi-switch"
    )
    
    switch = UbiquitiUnifiSwitch(device_info)
    features = switch.get_supported_features()
    
    # Check that we get a list of features
    assert isinstance(features, list)
    assert len(features) > 0
    
    # Check for some specific features
    feature_names = [f.name for f in features]
    assert "system_info_display" in feature_names
    assert "interfaces_status_table" in feature_names
    assert "vlan_brief_table" in feature_names


@patch('src.controllers.base.BaseDevice.connect')
@patch('src.controllers.base.BaseDevice.disconnect')
def test_ubiquiti_unifi_switch_context_manager(mock_disconnect, mock_connect):
    """Test that UbiquitiUnifiSwitch works as a context manager."""
    device_info = DeviceConnectionInfo(
        ip_address="192.168.1.1",
        device_type="ubiquiti_unifiswitch",
        username="admin",
        password="password",
        port=22,
        name="unifi-switch"
    )
    
    switch = UbiquitiUnifiSwitch(device_info)
    
    # Test context manager usage
    with switch:
        mock_connect.assert_called_once()
    
    mock_disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])