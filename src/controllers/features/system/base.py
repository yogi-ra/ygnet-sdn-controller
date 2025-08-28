from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

from ..base import BaseFeature


class BaseSystem(BaseFeature, ABC):
    """Abstract base class for system features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_version_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_hostname(self) -> str:
        pass

    @abstractmethod
    def get_active_users(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_local_users(self) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def get_clock(self) -> str:
        pass

    @abstractmethod
    def get_uptime(self) -> str:
        pass
