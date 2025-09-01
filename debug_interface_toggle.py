#!/usr/bin/env python3
"""
Debug script for interface toggle functionality
"""
import sys
import os
from src.device_info import DeviceConnectionInfo
from src.controllers.cisco_ios import CiscoIosSwitch

def test_interface_toggle():
    # Replace with actual device info for testing
    device_info = DeviceConnectionInfo(
        name="test-device",
        ip_address="192.168.1.1",  # Replace with actual IP
        port=22,
        device_type="cisco_ios_switch",
        username="admin",  # Replace with actual username
        password="password",  # Replace with actual password
        secret="secret"  # Replace with actual secret if needed
    )
    
    try:
        # Create device handler
        handler = CiscoIosSwitch(device_info)
        
        print("Connecting to device...")
        with handler:
            # Test getting interfaces brief
            print("Getting interfaces brief...")
            interfaces = handler.interfaces.get_interfaces_brief()
            print(f"Found {len(interfaces)} interfaces:")
            for interface in interfaces:
                print(f"  {interface.get('interface', 'N/A')}: status={interface.get('status', 'N/A')}, enabled={interface.get('enabled', 'N/A')}")
            
            if interfaces:
                # Test toggling the first interface
                test_interface = interfaces[0].get('interface')
                if test_interface:
                    print(f"\nTesting toggle for interface: {test_interface}")
                    
                    # Get current state
                    current_state = interfaces[0].get('enabled', None)
                    print(f"Current state: {current_state}")
                    
                    if current_state is not None:
                        # Toggle state
                        new_state = not current_state
                        print(f"Toggling to: {new_state}")
                        
                        result = handler.interfaces.set_interface_state(test_interface, new_state)
                        print(f"Toggle result: {result}")
                        
                        # Verify the change
                        print("Verifying change...")
                        new_interfaces = handler.interfaces.get_interfaces_brief()
                        for interface in new_interfaces:
                            if interface.get('interface') == test_interface:
                                print(f"New state: {interface.get('enabled', 'N/A')}")
                                break
                    else:
                        print("Could not determine current state, skipping toggle test")
                else:
                    print("No interface name found in first interface entry")
            else:
                print("No interfaces found")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_interface_toggle()