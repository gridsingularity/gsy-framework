"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class BidOfferMatch:
    """Representation of a market match."""
    market_id: str
    bids: List[Dict]
    selected_energy: float
    offers: List[Dict]
    trade_rate: float

    def serializable_dict(self) -> Dict:
        """Serialized representation of the instance."""
        return {
            "market_id": self.market_id,
            "bids": self.bids,
            "offers": self.offers,
            "selected_energy": self.selected_energy,
            "trade_rate": self.trade_rate
        }

    @classmethod
    def from_dict(cls, bid_offer_match: Dict) -> Optional["BidOfferMatch"]:
        """Receive a serializable dict of BidOfferMatch and return a BidOfferMatch object."""
        if cls.is_valid_dict(bid_offer_match):
            return BidOfferMatch(**bid_offer_match)

    @classmethod
    def is_valid_dict(cls, bid_offer_match: Dict) -> bool:
        """Check whether a serialized dict can be a valid BidOfferMatch instance."""
        is_valid = True
        if len(bid_offer_match.keys()) != len(cls.__annotations__.keys()):
            is_valid = False
        elif not all(attribute in bid_offer_match for attribute in cls.__annotations__):
            is_valid = False
        elif not isinstance(bid_offer_match["market_id"], str):
            is_valid = False
        elif not (isinstance(bid_offer_match["bids"], list) and
                  all(isinstance(bid, Dict) for bid in bid_offer_match["bids"])):
            is_valid = False
        elif not (isinstance(bid_offer_match["offers"], list) and
                  all(isinstance(offer, Dict) for offer in bid_offer_match["offers"])):
            is_valid = False
        elif not isinstance(bid_offer_match["selected_energy"], (int, float)):
            is_valid = False
        elif not isinstance(bid_offer_match["trade_rate"], (int, float)):
            is_valid = False
        return is_valid


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


@dataclass
class PlotDescription:
    data: list
    barmode: str
    xtitle: str
    ytitle: str
    title: str
