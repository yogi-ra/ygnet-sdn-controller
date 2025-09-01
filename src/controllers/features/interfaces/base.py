from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseInterfaces(BaseFeature, ABC):
    """Abstract base class for interface features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_interfaces_brief(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_interface_config(self, interface_name: str) -> Union[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_interfaces_status(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_interfaces_trunk(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_interface_vlan_membership(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_trunk_port_config(self, interface_name: str) -> Union[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_interface_port_security(self, interface_name: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def configure_interface(self, interface_name: str, config_commands: List[str]) -> Union[str, bool]:
        """
        Configures an interface with the provided commands.
        
        Args:
            interface_name: Name of the interface to configure
            config_commands: List of configuration commands to apply
            
        Returns:
            Output from configuration commands or boolean indicating success
        """
        pass