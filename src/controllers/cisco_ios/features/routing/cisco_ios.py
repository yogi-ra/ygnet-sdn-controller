from ....features.routing.base import BaseRouting
from typing import List, Dict, Any, Union

class CiscoIosRouting(BaseRouting):
    """Cisco IOS implementation of routing features."""

    def get_routing_table(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip route"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting routing table: {e}")
            return []

    def get_bgp_summary(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip bgp summary"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting BGP summary: {e}")
            return []

    def get_cdp_neighbors(self) -> List[Dict[str, Any]]:
        try:
            command = "show cdp neighbors detail"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting CDP neighbors: {e}")
            return []

    def get_lldp_neighbors(self) -> List[Dict[str, Any]]:
        try:
            command = "show lldp neighbors detail"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting LLDP neighbors: {e}")
            return []

    def get_ospf_neighbors(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip ospf neighbor"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting OSPF neighbors: {e}")
            return []

    def get_eigrp_neighbors(self) -> List[Dict[str, Any]]:
        try:
            command = "show ip eigrp neighbors"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting EIGRP neighbors: {e}")
            return []

    def get_routing_protocol_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | section router"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting routing protocol config: {e}")
            return ""

    def get_nat_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command = "show running-config | section ip nat"
            raw_output = self.device_handler.send_command(command)
            return self.device_handler.parse_cli_output(command, raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting NAT config: {e}")
            return ""

    def get_vpn_config(self) -> Union[List[Dict[str, Any]], str]:
        try:
            command_crypto = "show running-config | section crypto"
            raw_output_crypto = self.device_handler.send_command(command_crypto)

            command_tunnel = "show running-config | section tunnel"
            raw_output_tunnel = self.device_handler.send_command(command_tunnel)

            combined_raw_output = raw_output_crypto + "\n" + raw_output_tunnel
            return self.device_handler.parse_cli_output(command_crypto, combined_raw_output)
        except Exception as e:
            self.device_handler.logger.error(f"Error getting VPN config: {e}")
            return ""
