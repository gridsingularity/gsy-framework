from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BidOfferMatch:
    market_id: str
    bids: List[Dict]
    selected_energy: float
    offers: List[Dict]
    trade_rate: float

    def serializable_dict(self):
        return {
            "market_id": self.market_id,
            "bids": self.bids,
            "offers": self.offers,
            "selected_energy": self.selected_energy,
            "trade_rate": self.trade_rate
        }


@dataclass
class Clearing:
    rate: float
    energy: float

    def serializable_dict(self):
        return {
            "rate": self.rate,
            "energy": self.energy
        }


@dataclass
class MarketClearingState:
    cumulative_offers: Dict = field(default_factory=dict)
    cumulative_bids: Dict = field(default_factory=dict)
    clearing: Dict = field(default_factory=dict)

    @classmethod
    def _csv_fields(cls):
        return "time", "rate [ct./kWh]"
