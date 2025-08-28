from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseLldp(BaseFeature, ABC):
    """Abstract base class for LLDP features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_lldp_neighbors(self) -> Union[List[Dict[str, Any]], str]:
        pass
