from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ..base import BaseFeature


class BaseVlans(BaseFeature, ABC):
    """Abstract base class for VLAN features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_vlan_brief(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_vlan_details(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_vtp_status(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_vlan_config(self) -> List[Dict[str, Any]]:
        pass
