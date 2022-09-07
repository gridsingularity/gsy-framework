from abc import ABC, abstractmethod
from typing import Dict


class BaseAccumulator(ABC):
    """Base accumulator class."""
    @abstractmethod
    def __call__(self, last_results: Dict, collected_raw_data: Dict):
        """Calculate and return accumulated results."""


class EBEnergyTradeProfileAccumulator(BaseAccumulator):
    """Accumulator class for EB energy trade profile."""

    DEFAULT_STATS = {
        # SELLER
        "total_energy_produced_kWh": 0,
        "total_sell_trade_count": 0,
        "total_energy_sold_kWh": 0,
        "total_earned_eur": 0,
        # BUYER
        "total_energy_consumed_kWh": 0,
        "total_buy_trade_count": 0,
        "total_energy_bought_kWh": 0,
        "total_spent_eur": 0,
    }

    def __call__(self, last_results: Dict, collected_raw_data: Dict):
        last_results = last_results if last_results is not None else {}
        return self.handle_trades(last_results, collected_raw_data["trades"])

    def handle_trades(self, last_results, trades):
        """Handle traded stats of each device."""
        current_results = last_results

        for trade in trades:
            seller_id = trade["seller_id"]
            buyer_id = trade["buyer_id"]

            if seller_id not in current_results:
                current_results[seller_id] = dict(self.DEFAULT_STATS)

            if buyer_id not in current_results:
                current_results[buyer_id] = dict(self.DEFAULT_STATS)

            # SELLER
            current_results[seller_id]["total_energy_sold_kWh"] += trade["energy"]
            current_results[seller_id]["total_earned_eur"] += trade["price"]
            current_results[seller_id]["total_sell_trade_count"] += 1

            # BUYER
            current_results[buyer_id]["total_energy_bought_kWh"] += trade["energy"]
            current_results[buyer_id]["total_spent_eur"] += trade["price"]
            current_results[buyer_id]["total_buy_trade_count"] += 1

        return current_results
