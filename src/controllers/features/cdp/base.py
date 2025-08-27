from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseCDP(ABC):
    """Abstract base class for cdp features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_cdp_neighbors(self) -> List[Dict[str, Any]]:
        pass
