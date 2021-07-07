from abc import ABC, abstractmethod
from typing import Dict, List


class BaseMatchingAlgorithm(ABC):

    @classmethod
    @abstractmethod
    def get_matches_recommendations(cls, matching_data: Dict) -> List:
        """Calculate and return matches recommendations

        Args:
            matching_data: {market_uuid: {"offers": [...], "bids": [...], "current_time":"",...}}

        Returns: List[BidOfferMatch.serializable_dict()]
        """
