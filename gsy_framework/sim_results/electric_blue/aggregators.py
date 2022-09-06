from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict


class BaseAggregator(ABC):
    """Base accumulator class."""
    @abstractmethod
    def __call__(self, collected_raw_data: Dict):
        """Calculate and return accumulated results."""


class EBEnergyProfileAggregator(BaseAggregator):
    """Aggregator class for EB energy trade profile."""

    DEFAULT_STATS = {
        # open, still unmatched bids/offers
        "open_buy_orders": 0.0,
        "open_sell_orders": 0.0,
        # matched bids/offers
        "matched_buy_orders": 0.0,
        "matched_sell_orders": 0.0,
        # all
        "all_buy_orders": 0.0,
        "all_sell_orders": 0.0,
    }

    def __call__(self, collected_raw_data: Dict):
        current_result = defaultdict(lambda: dict(self.DEFAULT_STATS))

        for trade in collected_raw_data["trades"]:
            seller_id = trade["seller_id"]
            buyer_id = trade["buyer_id"]
            energy = trade["energy"]
            # SELLER
            current_result[seller_id]["matched_sell_orders"] += energy
            current_result[seller_id]["all_sell_orders"] += energy
            # BUYER
            current_result[buyer_id]["matched_buy_orders"] += energy
            current_result[buyer_id]["all_buy_orders"] += energy

        for bid in collected_raw_data["bids"]:
            buyer_id = bid["buyer_id"]
            energy = bid["energy"]
            # BUYER
            current_result[buyer_id]["open_buy_orders"] += energy
            current_result[buyer_id]["all_buy_orders"] += energy

        for offer in collected_raw_data["offers"]:
            seller_id = offer["seller_id"]
            energy = offer["energy"]
            # SELLER
            current_result[seller_id]["open_sell_orders"] += energy
            current_result[seller_id]["all_sell_orders"] += energy

        return current_result
