from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseArp(BaseFeature, ABC):
    """Abstract base class for ARP features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_arp_interface(self) -> Union[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_ip_arp(self) -> Union[List[Dict[str, Any]], str]:
        pass
