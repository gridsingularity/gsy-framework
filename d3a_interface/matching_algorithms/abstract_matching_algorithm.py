from abc import ABC, abstractmethod
from typing import Dict, List


class AbstractMatchingAlgorithm(ABC):

    @classmethod
    @abstractmethod
    def get_matches_recommendations(cls, bids_offers: Dict) -> List:
        """Calculate and return matches recommendations

        Args:
            bids_offers: dict {market_uuid: {"offers": [...], "bids": [...]}, }

        Returns: List[BidOfferMatch.serializable_dict()]
        """
