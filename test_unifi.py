#!/usr/bin/env python3
"""
Test script for Ubiquiti UniFi Switch controller implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.device_info import DeviceConnectionInfo
from src.controllers.ubiquiti_unifi import UbiquitiUnifiSwitch

def test_ubiquiti_unifi_switch_controller():
    # Use environment variables for device credentials
    device_ip = os.environ.get("SWITCH_HOST4")
    device_username = os.environ.get("SWITCH_USERNAME4")
    device_password = os.environ.get("SWITCH_PASSWORD4")
    
    if not all([device_ip, device_username, device_password]):
        print("Missing environment variables. Please set SWITCH_HOST4, SWITCH_USERNAME4, and SWITCH_PASSWORD4")
        return False
    
    # Create device info object with the new device type
    device_info = DeviceConnectionInfo(
        ip_address=device_ip,
        username=device_username,
        password=device_password,
        device_type="ubiquiti_unifiswitch",
        port=22
    )
    
    try:
        print(f"Testing Ubiquiti UniFi Switch controller at {device_info.ip_address}...")
        print(f"Device type: {device_info.device_type}")
        
        # Create controller instance
        controller = UbiquitiUnifiSwitch(device_info)
        print(f"Controller netmiko device type: {controller.netmiko_device_type}")
        
        # Test connection
        controller.connect()
        print("Connection established.")
        
        # Test a simple command to see what we get
        print("Testing simple command...")
        output = controller.send_command("show version")
        print(f"Raw output:\n{output}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ubiquiti_unifi_switch_controller()