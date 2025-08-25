from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class BaseInterfaces(ABC):
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
