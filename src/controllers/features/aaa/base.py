from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseAaa(BaseFeature, ABC):
    """Abstract base class for AAA features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_aaa_config(self) -> Union[List[Dict[str, Any]], str]:
        pass
