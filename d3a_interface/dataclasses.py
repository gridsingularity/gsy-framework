from dataclasses import dataclass


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
