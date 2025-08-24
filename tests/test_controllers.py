import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.controllers import (
    DeviceConnectionInfo,
    get_device_handler,
    CiscoIosRouter,
    CiscoIosSwitch,
)


@pytest.fixture
def sample_cisco_router_info():
    """Provides a sample DeviceConnectionInfo object for a Cisco IOS Router device."""
    return DeviceConnectionInfo(
        name="router.example.com",
        ip_address="10.100.100.2",
        device_type="cisco_ios_router",
        username="testuser",
        password="testpass",
        secret="testsecret",
    )


@pytest.fixture
def sample_cisco_switch_info():
    """Provides a sample DeviceConnectionInfo object for a Cisco IOS Switch device."""
    return DeviceConnectionInfo(
        name="switch.example.com",
        ip_address="10.100.100.3",
        device_type="cisco_ios_switch",
        username="testuser",
        password="testpass",
        secret="testsecret",
    )


# --- Factory Tests ---
def test_get_device_handler_returns_correct_router_class(sample_cisco_router_info):
    """Test that the factory returns an instance of the correct router class."""
    handler = get_device_handler(sample_cisco_router_info)
    assert isinstance(handler, CiscoIosRouter)


def test_get_device_handler_returns_correct_switch_class(sample_cisco_switch_info):
    """Test that the factory returns an instance of the correct switch class."""
    handler = get_device_handler(sample_cisco_switch_info)
    assert isinstance(handler, CiscoIosSwitch)


def test_get_device_handler_raises_error_for_unsupported_type(sample_cisco_router_info):
    """Test that the factory raises NotImplementedError for an unsupported device type."""
    sample_cisco_router_info.device_type = "unsupported_os"
    with pytest.raises(NotImplementedError, match="'unsupported_os' is not supported"):
        get_device_handler(sample_cisco_router_info)

