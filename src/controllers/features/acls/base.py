from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

class BaseAcls(ABC):
    """Abstract base class for ACL features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_acls(self) -> Union[List[Dict[str, Any]], str]:
        pass
