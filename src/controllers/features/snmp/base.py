from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class BaseSnmp(ABC):
    """Abstract base class for SNMP features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_snmp_config(self) -> Union[List[Dict[str, Any]], str]:
        pass
