from dataclasses import dataclass, field


@dataclass
class BidOfferMatch:
    market_id: str
    bid: dict
    selected_energy: float
    offer: dict
    trade_rate: float

    def serializable_dict(self):
        return {
            "market_id": self.market_id,
            "bid": self.bid,
            "offer": self.offer,
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
    cumulative_offers: dict = field(default_factory=dict)
    cumulative_bids: dict = field(default_factory=dict)
    clearing: dict = field(default_factory=dict)

    @classmethod
    def _csv_fields(cls):
        return "time", "rate [ct./kWh]"
