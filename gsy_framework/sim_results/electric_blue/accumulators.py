from abc import ABC, abstractmethod
from typing import Dict


class BaseAccumulator(ABC):
    """Base accumulator class."""
    @abstractmethod
    def __call__(self, collected_raw_data: Dict, last_results: Dict = None):
        """Calculate and return accumulated results."""


class EBEnergyTradeProfile(BaseAccumulator):
    """Accumulator class for EB energy trade profile."""
    def __call__(self, collected_raw_data: Dict, last_results: Dict = None):
        return {}
