import uuid
from abc import ABC, abstractmethod

from typing import Optional, List
from pendulum import DateTime
from gsy_framework.data_classes import Bid, Offer, Trade


class TwoSidedMarketInterface(ABC):
    """
    Define a common interface for two-sided market access for the centralized and decentralized
    exchanges.
    """
    def __init__(self):
        self._market_id = uuid.uuid4()

    @abstractmethod
    def post_bid(
            self, price: float, energy: float,
            buyer: str, buyer_origin: str,
            buyer_origin_id: Optional[str] = None,
            buyer_id: Optional[str] = None,
            time_slot: Optional[DateTime] = None
            # priority: int, energy_type: List[int],
            # attributes: List[List[int]],
            # pref_partners: Optional[List[str]] = None,
            # attributes: Optional[Dict] = None,
            # requirements: Optional[List[Dict]] = None,
            ) -> Optional[Bid]:  # TODO: Define the DEX desired return type
        """Post a new bid to the market."""

    @abstractmethod
    def delete_bids(self, bids: List[Bid]) -> None:
        """Delete a list of bids from the market."""

    @abstractmethod
    def get_bids(self) -> List[Bid]:
        """Retrieve all open bids from the market."""

    @abstractmethod
    def post_offer(
            self, price: float, energy: float,
            seller: str, seller_origin: str,
            seller_origin_id: Optional[str] = None,
            seller_id: Optional[str] = None,
            time_slot: Optional[DateTime] = None,
            # TODO: Find out if needed or is possible to circumvent
            # dispatch_event: bool = True,
            # attributes: Optional[Dict] = None,
            # requirements: Optional[List[Dict]] = None
            # attributes: List[List[int]],
            # priority: int, energy_type: List[int],
            # pref_partners: Optional[List[str]] = None,
    ) -> Optional[Offer]:
        """Post a new offer to the market."""

    @abstractmethod
    def delete_offers(self, offers: List[Offer]) -> None:  # TODO: Possibly return a Future object
        """Delete a list of offers from the market."""

    @abstractmethod
    def get_offers(self) -> List[Offer]:
        """Retrieve all open offers from the market."""

    @abstractmethod
    def get_trades(self) -> List[Trade]:
        """Retrieve all executed trades on the market."""
