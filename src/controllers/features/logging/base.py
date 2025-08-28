from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union

from ..base import BaseFeature


class BaseLogging(BaseFeature, ABC):
    """Abstract base class for logging features."""

    def __init__(self, device_handler):
        self.device_handler = device_handler

    @abstractmethod
    def get_logging_config(self) -> Union[List[Dict[str, Any]], str]:
        pass
