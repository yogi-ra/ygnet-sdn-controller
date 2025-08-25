from .base import BaseDevice
from typing import List, Dict, Any, Union
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class CiscoIosDevice(BaseDevice):
    """
    Base handler for Cisco IOS devices with common methods.
    This class is not meant to be instantiated directly, but serves as a base
    for more specific Cisco IOS device types (e.g., Router, Switch).
    """

    @property
    def netmiko_device_type(self) -> str:
        """
        Returns the Netmiko device_type string for Cisco IOS devices.
        All Cisco IOS devices use 'cisco_ios' for Netmiko.
        """
        return "cisco_ios"

    def get_version_info(self) -> Dict[str, Any]:
        """
        Gets structured version and system information.

        Returns:
            A dictionary containing parsed version information.
        """
        command = "show version"
        raw_output = self.send_command(command)
        version_data = self.parse_cli_output(command, raw_output)
        if version_data and isinstance(version_data, list):
            return version_data[0]
        return {}

    def get_interfaces_brief(self) -> List[Dict[str, Any]]:
        """
        Gets a brief list of IP interfaces and their status.

        Returns:
            A list of dictionaries, each representing an interface.
        """
        command = "show ip interface brief"
        raw_output = self.send_command(command)
        logger.debug(f"Raw output for 'show ip interface brief':\n{raw_output}")
        return self.parse_cli_output(command, raw_output)

    def get_active_users(self) -> List[Dict[str, Any]]:
        """
        Gets a list of currently logged-in users (active sessions).

        Returns:
            A list of dictionaries, each representing an active user session.
        """
        command = "show users"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_local_users(self) -> List[Dict[str, str]]:
        """
        Retrieves local user accounts configured on the Cisco IOS device.
        Returns a list of dictionaries, each containing the username
        and optionally the privilege level.
        """
        command = "show running-config | include ^username"
        output = self.send_command(command=command)
        lines = output.strip().splitlines()

        results = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                username = parts[1]
                user_data = {"username": username}

                match = re.search(r'privilege\s+(\d+)', line)
                if match:
                    user_data["privilege"] = match.group(1)

                results.append(user_data)

        return results

    def get_clock(self) -> datetime:
        """
        Gets the current time from the device and parses it into a datetime object.

        Returns:
            A datetime object representing the device's current time.
        """
        output = self.send_command(command="show clock")
        # Example output: "*13:26:03.945 UTC Thu Aug 21 2025"
        # Format: "*%H:%M:%S.%f UTC %a %b %d %Y"
        try:
            # Remove the leading asterisk if present
            if output.startswith("*"):
                output = output[1:].strip()
            # Handle potential timezone variations or simplify for UTC
            # For simplicity, assuming UTC and parsing directly
            # The format string needs to match the exact output format
            # Note: %f is for microseconds, if milliseconds are present, it might need adjustment
            # For now, let's assume the format is consistent with the example
            return datetime.strptime(output, "%H:%M:%S.%f UTC %a %b %d %Y")
        except ValueError:
            # Fallback or raise a more specific error if parsing fails
            # For now, re-raising to indicate a parsing issue
            raise ValueError(f"Failed to parse clock output: {output}")

    def get_hostname(self) -> str:
        """
        Extracts the hostname from the 'show version' output.

        Returns:
            The device hostname as a string.
        """
        version_info = self.get_version_info()
        return version_info.get("hostname", "")

    def get_interface_config(
        self, interface_name: str
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the configuration for a specific interface.
        Uses parse_cli_output for structured parsing with fallback.

        Args:
            interface_name: The name of the interface (e.g., 'GigabitEthernet0/1').
        """
        command = f"show running-config interface {interface_name}"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_line_config(self) -> List[str]:
        """
        Gets the line configuration (vty, console) from the running configuration.

        Returns:
            A list of strings, where each string is a line of the line configuration.
        """
        output = self.send_command(command="show running-config | section line")
        return output.splitlines()

    def get_banners(self) -> Union[Dict[str, str], str]:
        """
        Gets the banners (MOTD, login) from the running configuration.
        Attempts custom Python parsing, then falls back to parse_cli_output.
        """
        command = "show running-config | section banner"
        raw_output = self.send_command(command)

        banners = {}
        current_banner_type = None
        current_banner_lines = []

        lines = raw_output.splitlines()

        for line in lines:
            line = line.strip()
            if line.startswith("banner motd"):
                if current_banner_type and current_banner_lines:
                    banners[current_banner_type] = "\n".join(current_banner_lines)
                current_banner_type = "motd"
                current_banner_lines = []
                delimiter = line[len("banner motd ") :].strip()[0]
                continue
            elif line.startswith("banner login"):
                if current_banner_type and current_banner_lines:
                    banners[current_banner_type] = "\n".join(current_banner_lines)
                current_banner_type = "login"
                current_banner_lines = []
                delimiter = line[len("banner login ") :].strip()[0]
                continue
            elif line.startswith("banner exec"):
                if current_banner_type and current_banner_lines:
                    banners[current_banner_type] = "\n".join(current_banner_lines)
                current_banner_type = "exec"
                current_banner_lines = []
                delimiter = line[len("banner exec ") :].strip()[0]
                continue

            if current_banner_type:
                if line == delimiter:
                    banners[current_banner_type] = "\n".join(current_banner_lines)
                    current_banner_type = None
                    current_banner_lines = []
                else:
                    current_banner_lines.append(line)

        if current_banner_type and current_banner_lines:
            banners[current_banner_type] = "\n".join(current_banner_lines)

        if banners:
            return banners

        # Fallback to parse_cli_output if custom parsing fails
        return self.parse_cli_output(command, raw_output)

    def get_ntp_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the NTP configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | include ntp"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_snmp_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the SNMP configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | include snmp-server"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_logging_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the logging configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | include logging"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_acls(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the Access Control Lists (ACLs) from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | section access-list"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_aaa_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the AAA (Authentication, Authorization, and Accounting) configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | section aaa"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)


class CiscoIosRouter(CiscoIosDevice):
    """Handler for Cisco IOS Router devices."""

    def get_routing_table(self) -> List[Dict[str, Any]]:
        """
        Gets the IP routing table.
        """
        command = "show ip route"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_bgp_summary(self) -> List[Dict[str, Any]]:
        """
        Gets the BGP summary information.
        """
        command = "show ip bgp summary"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_cdp_neighbors(self) -> List[Dict[str, Any]]:
        """
        Gets the CDP (Cisco Discovery Protocol) neighbors.

        Returns:
            A list of dictionaries, each representing a CDP neighbor.
        """
        command = "show cdp neighbors detail"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_lldp_neighbors(self) -> List[Dict[str, Any]]:
        """
        Gets the LLDP (Link Layer Discovery Protocol) neighbors.

        Returns:
            A list of dictionaries, each representing an LLDP neighbor.
        """
        command = "show lldp neighbors detail"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_ospf_neighbors(self) -> List[Dict[str, Any]]:
        """
        Gets the OSPF (Open Shortest Path First) neighbors.

        Returns:
            A list of dictionaries, each representing an OSPF neighbor.
        """
        command = "show ip ospf neighbor"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_eigrp_neighbors(self) -> List[Dict[str, Any]]:
        """
        Gets the EIGRP (Enhanced Interior Gateway Routing Protocol) neighbors.

        Returns:
            A list of dictionaries, each representing an EIGRP neighbor.
        """
        command = "show ip eigrp neighbors"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_routing_protocol_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the routing protocol configuration (OSPF, EIGRP, RIP) from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | section router"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_nat_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the NAT (Network Address Translation) configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | section ip nat"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_vpn_config(self) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the VPN (IPsec, GRE) configuration from the running configuration.
        Attempts custom Python parsing, then falls back to parse_cli_output.
        """
        command_crypto = "show running-config | section crypto"
        raw_output_crypto = self.send_command(command_crypto)

        command_tunnel = "show running-config | section tunnel"
        raw_output_tunnel = self.send_command(command_tunnel)

        combined_raw_output = raw_output_crypto + "\n" + raw_output_tunnel

        # Custom parsing for VPN config (example - needs to be robust)
        vpn_config_data = []
        lines = combined_raw_output.splitlines()

        # Example: Look for "crypto isakmp policy" or "tunnel mode"
        for line in lines:
            line = line.strip()
            if line.startswith("crypto isakmp policy"):
                vpn_config_data.append({"type": "isakmp_policy", "config": line})
            elif line.startswith("tunnel mode"):
                vpn_config_data.append({"type": "tunnel_mode", "config": line})
            # Add more parsing logic here

        if vpn_config_data:
            return vpn_config_data

        # Fallback: Return combined raw output if custom parsing yields no data
        return combined_raw_output


class CiscoIosSwitch(CiscoIosDevice):
    """Handler for Cisco IOS Switch devices."""

    def get_vlan_brief(self) -> List[Dict[str, Any]]:
        """
        Gets a brief summary of VLANs.
        """
        command = "show vlan brief"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_mac_address_table(self) -> List[Dict[str, Any]]:
        """
        Gets the MAC address table.
        """
        command = "show mac address-table"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_interfaces_status(self) -> List[Dict[str, Any]]:
        """
        Gets the status of all interfaces on the switch.
        """
        command = "show interfaces status"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_vlan_details(self) -> List[Dict[str, Any]]:
        """
        Gets detailed information about VLANs.
        """
        command = "show vlan"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_vtp_status(self) -> List[Dict[str, Any]]:
        """
        Gets the VTP (VLAN Trunking Protocol) status.
        """
        command = "show vtp status"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_spanning_tree_summary(self) -> List[Dict[str, Any]]:
        """
        Gets a summary of the Spanning Tree Protocol (STP) status.
        Attempts to parse using Netmiko's TextFSM, then falls back to custom Python parsing,
        and finally to an empty list if all parsing fails.
        """
        command = "show spanning-tree summary"
        raw_output = self.send_command(command)
        try:
            # Attempt 1: Netmiko's send_command_and_parse
            parsed_output = self.parse_cli_output(command, raw_output)
            if parsed_output:
                return parsed_output
        except Exception as e:
            # Log the exception if needed
            pass  # Continue to fallback parsing

        # Attempt 2: Custom Python-based parsing
        # Use the raw_output from the first send_command call

        # Simple parsing for VLAN table
        vlan_data = []
        lines = raw_output.splitlines()

        # Find the start of the VLAN table
        table_start_index = -1
        for i, line in enumerate(lines):
            if "Name" in line and "STP Active" in line:
                table_start_index = i
                break

        if table_start_index != -1:
            # Skip header and separator lines
            for line in lines[table_start_index + 2 :]:
                if (
                    "---" in line or "vlans" in line
                ):  # Stop at separator or summary line
                    break
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        vlan_name = parts[0]
                        blocking = int(parts[1])
                        listening = int(parts[2])
                        learning = int(parts[3])
                        forwarding = int(parts[4])
                        stp_active = int(parts[5])
                        vlan_data.append(
                            {
                                "vlan_name": vlan_name,
                                "blocking": blocking,
                                "listening": listening,
                                "learning": learning,
                                "forwarding": forwarding,
                                "stp_active": stp_active,
                            }
                        )
                    except ValueError:
                        # Skip lines that don't parse as expected
                        continue

        if vlan_data:
            return vlan_data

        # Fallback 3: Return empty list if all parsing fails
        return []

    def get_interfaces_trunk(self) -> List[Dict[str, Any]]:
        """
        Gets information about trunking interfaces.
        Attempts to parse using Netmiko's TextFSM, then falls back to custom Python parsing,
        and finally to an empty list if all parsing fails.
        """
        command = "show interfaces trunk"
        raw_output = self.send_command(command)
        try:
            # Attempt 1: Netmiko's send_command_and_parse
            parsed_output = self.parse_cli_output(command, raw_output)
            if parsed_output:
                return parsed_output
        except Exception as e:
            # Log the exception if needed
            pass  # Continue to fallback parsing

        # Attempt 2: Custom Python-based parsing
        # Use the raw_output from the first send_command call

        # Simple parsing for trunk interfaces
        trunk_data = []
        lines = raw_output.splitlines()

        # Example output:
        # Port        Mode         Encapsulation  Status        Native VLAN
        # Gi0/1       on           802.1q         trunking      1

        for line in lines:
            if "trunking" in line and "802.1q" in line:
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        port = parts[0]
                        mode = parts[1]
                        encapsulation = parts[2]
                        status = parts[3]
                        native_vlan = parts[4]
                        trunk_data.append(
                            {
                                "port": port,
                                "mode": mode,
                                "encapsulation": encapsulation,
                                "status": status,
                                "native_vlan": native_vlan,
                            }
                        )
                    except ValueError:
                        continue

        if trunk_data:
            return trunk_data

        # Fallback 3: Return empty list if all parsing fails
        return []

    def get_port_security(self) -> List[Dict[str, Any]]:
        """
        Gets the port security configuration.

        Returns:
            A list of dictionaries, each representing port security information.
        """
        command = "show port-security"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_etherchannel_summary(self) -> List[Dict[str, Any]]:
        """
        Gets the EtherChannel summary.

        Returns:
            A list of dictionaries, each representing EtherChannel summary information.
        """
        command = "show etherchannel summary"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_vlan_config(self) -> List[Dict[str, Any]]:
        """
        Gets the detailed VLAN configuration from the running configuration.
        Uses parse_cli_output for structured parsing with fallback.
        """
        command = "show running-config | section vlan"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_interface_vlan_membership(self) -> List[Dict[str, Any]]:
        """
        Gets the interface VLAN membership information.

        Returns:
            A list of dictionaries, each representing interface VLAN membership.
        """
        command = "show interface switchport"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_trunk_port_config(
        self, interface_name: str
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Gets the detailed trunk port configuration for a specific interface.
        Uses parse_cli_output for structured parsing with fallback.

        Args:
            interface_name: The name of the interface (e.g., 'GigabitEthernet0/1').
        """
        command = f"show interfaces {interface_name} switchport"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)

    def get_interface_port_security(self, interface_name: str) -> List[Dict[str, Any]]:
        """
        Gets the port security configuration for a specific interface.
        """
        command = f"show port-security interface {interface_name}"
        raw_output = self.send_command(command)
        return self.parse_cli_output(command, raw_output)
