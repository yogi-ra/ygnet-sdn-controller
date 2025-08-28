from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseRouting(BaseFeature, ABC):
    """Abstract base class for routing features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_routing_table(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_bgp_summary(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_cdp_neighbors(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_lldp_neighbors(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_ospf_neighbors(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_eigrp_neighbors(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_routing_protocol_config(self) -> Union[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_nat_config(self) -> Union[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_vpn_config(self) -> Union[List[Dict[str, Any]], str]:
        pass
