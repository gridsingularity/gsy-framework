"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

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
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
# pylint: disable=no-member

import json
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Union

from pendulum import DateTime

from gsy_framework.constants_limits import DEFAULT_PRECISION
from gsy_framework.utils import (
    limit_float_precision, datetime_to_string_incl_seconds, key_in_dict_and_not_none,
    str_to_pendulum_datetime)


def json_datetime_serializer(datetime_obj: DateTime) -> Optional[str]:
    """Define how to convert datetime objects while serializing to json."""
    if isinstance(datetime_obj, DateTime):
        return datetime_to_string_incl_seconds(datetime_obj)
    return None


class BaseBidOffer:
    """Base class defining shared functionality of Bid and Offer market structures."""
    def __init__(self, id: str, creation_time: DateTime, price: float, energy: float,
                 original_price: Optional[float] = None, time_slot: DateTime = None,
                 attributes: Dict = None, requirements: List[Dict] = None):
        self.id = str(id)
        self.creation_time = creation_time
        self.time_slot = time_slot  # market slot of creation
        self.original_price = original_price or price
        self.price = price
        self.energy = energy
        self.attributes = attributes
        self.requirements = requirements
        self.type = self.__class__.__name__

    @property
    def energy_rate(self) -> float:
        """Dynamically calculate rate of energy."""
        return limit_float_precision(self.price / self.energy)

    def update_price(self, price: float) -> None:
        """Update price member."""
        self.price = price

    def update_energy(self, energy: float) -> None:
        """Update energy member."""
        self.energy = energy

    def to_json_string(self, **kwargs) -> str:
        """Convert the Offer or Bid object into its JSON representation.

        Args:
            **kwargs: additional key-value pairs to be added to the JSON representation.
        """
        obj_dict = deepcopy(self.__dict__)
        if kwargs:
            obj_dict = {**obj_dict, **kwargs}

        obj_dict["energy_rate"] = self.energy_rate
        return json.dumps(obj_dict, default=json_datetime_serializer)

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "type": self.type,
            "id": self.id,
            "energy": self.energy,
            "energy_rate": self.energy_rate,
            "original_price": self.original_price,
            "creation_time": datetime_to_string_incl_seconds(self.creation_time),
            "time_slot": datetime_to_string_incl_seconds(self.time_slot),
            "attributes": self.attributes,
            "requirements": self.requirements
        }

    @classmethod
    def from_json(cls, offer_or_bid: str) -> Union["Offer", "Bid"]:
        """De-serialize orders from json string."""
        offer_bid_dict = json.loads(offer_or_bid)
        object_type = offer_bid_dict.pop("type", None)
        if not object_type:
            assert False, "from_json expects a json string containing the 'type' key"
        offer_bid_dict.pop("energy_rate", None)
        if offer_bid_dict.get("creation_time"):
            offer_bid_dict["creation_time"] = (
                str_to_pendulum_datetime(offer_bid_dict["creation_time"]))
        else:
            offer_bid_dict["creation_time"] = None
        if offer_bid_dict.get("time_slot"):
            offer_bid_dict["time_slot"] = str_to_pendulum_datetime(offer_bid_dict["time_slot"])
        if object_type == "Offer":
            return Offer(**offer_bid_dict)
        if object_type == "Bid":
            return Bid(**offer_bid_dict)
        assert False, "the type member needs to be set to one of ('Bid', 'Offer')."

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the order."""
        return 0


class Offer(BaseBidOffer):
    """Offer class"""
    def __init__(self, id: str, creation_time: DateTime, price: float,
                 energy: float, seller: str, original_price: Optional[float] = None,
                 seller_origin: str = None, seller_origin_id: str = None,
                 seller_id: str = None,
                 attributes: Dict = None,
                 requirements: List[Dict] = None,
                 time_slot: DateTime = None):
        super().__init__(id=id, creation_time=creation_time, price=price, energy=energy,
                         original_price=original_price,
                         attributes=attributes, requirements=requirements, time_slot=time_slot)
        self.seller = seller
        self.seller_origin = seller_origin
        self.seller_origin_id = seller_origin_id
        self.seller_id = seller_id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"<Offer('{self.id!s:.6s}', '{self.energy} kWh@{self.price}',"
            f" '{self.seller} {self.energy_rate}'>")

    def __str__(self) -> str:
        return (f"{{{self.id!s:.6s}}} [origin: {self.seller_origin}] "
                f"[{self.seller}]: {self.energy} kWh @ {self.price} @ {self.energy_rate}")

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {**super().serializable_dict(),
                "seller": self.seller,
                "seller_origin": self.seller_origin,
                "seller_origin_id": self.seller_origin_id,
                "seller_id": self.seller_id,
                }

    @staticmethod
    def from_dict(offer: Dict) -> "Offer":
        """Deserialize an offer dict."""

        return Offer(
            id=offer["id"],
            creation_time=str_to_pendulum_datetime(offer["creation_time"]),
            time_slot=str_to_pendulum_datetime(offer["time_slot"]),
            energy=offer["energy"],
            price=offer["energy"] * offer["energy_rate"],
            original_price=offer.get("original_price"),
            seller=offer.get("seller"),
            seller_origin=offer.get("seller_origin"),
            seller_origin_id=offer.get("seller_origin_id"),
            seller_id=offer.get("seller_id"),
            attributes=offer.get("attributes"),
            requirements=offer.get("requirements"))

    def __eq__(self, other) -> bool:
        return (self.id == other.id and
                self.seller == other.seller and
                self.seller_origin_id == other.seller_origin_id and
                self.attributes == other.attributes and
                self.requirements == other.requirements and
                self.creation_time == other.creation_time and
                self.time_slot == other.time_slot)

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.energy_rate, 4)
        return self.creation_time, rate, self.energy, self.price, self.seller

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return "creation_time", "rate [ct./kWh]", "energy [kWh]", "price [ct.]", "seller"

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the offer."""
        return self.price - self.original_price

    @staticmethod
    def copy(offer: "Offer") -> "Offer":
        """Return a copy of an offer Object."""
        return Offer(offer.id, offer.creation_time, offer.price, offer.energy, offer.seller,
                     offer.original_price, offer.seller_origin, offer.seller_origin_id,
                     offer.seller_id, attributes=offer.attributes, requirements=offer.requirements,
                     time_slot=offer.time_slot)


class Bid(BaseBidOffer):
    """Bid class."""
    def __init__(self, id: str, creation_time: DateTime, price: float,
                 energy: float, buyer: str,
                 original_price: Optional[float] = None,
                 buyer_origin: str = None,
                 buyer_origin_id: str = None,
                 buyer_id: str = None,
                 attributes: Dict = None,
                 requirements: List[Dict] = None,
                 time_slot: Optional[DateTime] = None
                 ):
        super().__init__(id=id, creation_time=creation_time, price=price, energy=energy,
                         original_price=original_price,
                         attributes=attributes, requirements=requirements, time_slot=time_slot)
        self.buyer = buyer
        self.buyer_origin = buyer_origin
        self.buyer_origin_id = buyer_origin_id
        self.buyer_id = buyer_id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"<Bid {{{self.id!s:.6s}}} [{self.buyer}] "
            f"{self.energy} kWh @ {self.price} {self.energy_rate}>"
        )

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [origin: {self.buyer_origin}] [{self.buyer}] "
            f"{self.energy} kWh @ {self.price} {self.energy_rate}"
        )

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {**super().serializable_dict(),
                "buyer_origin": self.buyer_origin,
                "buyer_origin_id": self.buyer_origin_id,
                "buyer_id": self.buyer_id,
                "buyer": self.buyer,
                }

    @staticmethod
    def from_dict(bid: Dict) -> "Bid":
        """Deserialize a bid dict."""

        return Bid(
            id=bid["id"],
            creation_time=str_to_pendulum_datetime(bid["creation_time"]),
            energy=bid["energy"],
            price=bid["energy"] * bid["energy_rate"],
            original_price=bid.get("original_price"),
            buyer=bid.get("buyer"),
            buyer_origin=bid.get("buyer_origin"),
            buyer_origin_id=bid.get("buyer_origin_id"),
            buyer_id=bid.get("buyer_id"),
            attributes=bid.get("attributes"),
            requirements=bid.get("requirements"),
            time_slot=str_to_pendulum_datetime(bid.get("time_slot"))
        )

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.energy_rate, 4)
        return self.creation_time, rate, self.energy, self.price, self.buyer

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return "creation_time", "rate [ct./kWh]", "energy [kWh]", "price [ct.]", "buyer"

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the bid."""
        return self.original_price - self.price

    def __eq__(self, other) -> bool:
        return (self.id == other.id and
                self.buyer == other.buyer and
                self.buyer_origin_id == other.buyer_origin_id and
                self.attributes == other.attributes and
                self.requirements == other.requirements and
                self.creation_time == other.creation_time and
                self.time_slot == other.time_slot)


@dataclass
class TradeBidOfferInfo:
    """Class that contains information about the original bid or offer."""
    original_bid_rate: Optional[float]
    propagated_bid_rate: Optional[float]
    original_offer_rate: Optional[float]
    propagated_offer_rate: Optional[float]
    trade_rate: Optional[float]
    matching_requirements: Optional[Dict] = None

    def to_json_string(self) -> str:
        """Return json string of the representation."""
        return json.dumps(asdict(self), default=json_datetime_serializer)

    @staticmethod
    def from_json(trade_bid_offer_info: str) -> "TradeBidOfferInfo":
        """Return TradeBidOfferInfo object from json representation."""
        info_dict = json.loads(trade_bid_offer_info)
        return TradeBidOfferInfo(**info_dict)


class Trade:
    """Trade class."""
    def __init__(self, id: str, creation_time: DateTime, offer_bid: Union[Offer, Bid],
                 seller: str, buyer: str,
                 traded_energy: float, trade_price: float,
                 residual: Optional[Union[Offer, Bid]] = None,
                 already_tracked: bool = False,
                 offer_bid_trade_info: Optional[TradeBidOfferInfo] = None,
                 seller_origin: Optional[str] = None, buyer_origin: Optional[str] = None,
                 fee_price: Optional[float] = None, seller_origin_id: Optional[str] = None,
                 buyer_origin_id: Optional[str] = None, seller_id: Optional[str] = None,
                 buyer_id: Optional[str] = None, time_slot: Optional[DateTime] = None,
                 matching_requirements: Optional[Dict] = None):

        self.id = str(id)
        self.creation_time = creation_time
        self.time_slot = time_slot  # market slot of creation
        self.offer_bid = offer_bid
        self.seller = seller
        self.buyer = buyer
        self.traded_energy = traded_energy
        self.trade_price = trade_price
        self.residual = residual
        self.already_tracked = already_tracked
        self.offer_bid_trade_info = offer_bid_trade_info
        self.seller_origin = seller_origin
        self.buyer_origin = buyer_origin
        self.fee_price = fee_price
        self.seller_origin_id = seller_origin_id
        self.buyer_origin_id = buyer_origin_id
        self.seller_id = seller_id
        self.buyer_id = buyer_id
        self.matching_requirements = matching_requirements

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [origin: {self.seller_origin} -> {self.buyer_origin}] "
            f"[{self.seller} -> {self.buyer}] {self.traded_energy} kWh @ {self.trade_price}"
            f" {round(self.trade_rate, 8)} "
            f"{self.offer_bid.id} [fee: {self.fee_price} cts.] "
            f"{self.matching_requirements or ''}")

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return ("creation_time", "rate [ct./kWh]", "energy [kWh]", "seller", "buyer",
                "matching_requirements")

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.trade_rate, 4)
        return (self.creation_time, rate, self.traded_energy, self.seller, self.buyer,
                self.matching_requirements)

    def to_json_string(self) -> str:
        """Return json string of the representation."""
        # __dict__ instead of asdict to not recursively deserialize objects
        trade_dict = deepcopy(self.__dict__)
        trade_dict["offer_bid"] = trade_dict["offer_bid"].to_json_string()
        if key_in_dict_and_not_none(trade_dict, "residual"):
            trade_dict["residual"] = trade_dict["residual"].to_json_string()
        if key_in_dict_and_not_none(trade_dict, "offer_bid_trade_info"):
            trade_dict["offer_bid_trade_info"] = (
                trade_dict["offer_bid_trade_info"].to_json_string())
        return json.dumps(trade_dict, default=json_datetime_serializer)

    @classmethod
    def from_json(cls, trade_string) -> "Trade":
        """De-serialize trade from json string."""
        trade_dict = json.loads(trade_string)
        trade_dict["offer_bid"] = BaseBidOffer.from_json(trade_dict["offer_bid"])
        if trade_dict.get("residual"):
            trade_dict["residual"] = BaseBidOffer.from_json(trade_dict["residual"])
        if trade_dict.get("creation_time"):
            trade_dict["creation_time"] = str_to_pendulum_datetime(trade_dict["creation_time"])
        else:
            trade_dict["creation_time"] = None
        if trade_dict.get("time_slot"):
            trade_dict["time_slot"] = str_to_pendulum_datetime(trade_dict["time_slot"])
        if trade_dict.get("offer_bid_trade_info"):
            trade_dict["offer_bid_trade_info"] = (
                TradeBidOfferInfo.from_json(trade_dict["offer_bid_trade_info"]))
        return Trade(**trade_dict)

    @property
    def is_bid_trade(self) -> bool:
        """Check if the instance is a bid trade."""
        return isinstance(self.offer_bid, Bid)

    @property
    def is_offer_trade(self) -> bool:
        """Check if the instance is an offer trade."""
        return isinstance(self.offer_bid, Offer)

    @property
    def trade_rate(self):
        """Return the energy rate of the trade."""
        return round(self.trade_price / self.traded_energy, DEFAULT_PRECISION)

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "type": "Trade",
            "match_type": type(self.offer_bid).__name__,
            "id": self.id,
            "offer_bid_id": self.offer_bid.id,
            "residual_id": self.residual.id if self.residual is not None else None,
            "energy": self.traded_energy,
            "energy_rate": self.trade_rate,
            "price": self.trade_price,
            "buyer": self.buyer,
            "buyer_origin": self.buyer_origin,
            "seller_origin": self.seller_origin,
            "seller_origin_id": self.seller_origin_id,
            "buyer_origin_id": self.buyer_origin_id,
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "seller": self.seller,
            "fee_price": self.fee_price,
            "creation_time": datetime_to_string_incl_seconds(self.creation_time),
            "time_slot": datetime_to_string_incl_seconds(self.time_slot),
        }

    def __eq__(self, other: "Trade") -> bool:
        return (
            self.id == other.id and
            self.creation_time == other.creation_time and
            self.time_slot == other.time_slot and
            self.offer_bid == other.offer_bid and
            self.traded_energy == other.traded_energy and
            self.trade_price == other.trade_price and
            self.seller == other.seller and
            self.buyer == other.buyer and
            self.residual == other.residual and
            self.already_tracked == other.already_tracked and
            self.offer_bid_trade_info == other.offer_bid_trade_info and
            self.seller_origin == other.seller_origin and
            self.buyer_origin == other.buyer_origin and
            self.seller_origin_id == other.seller_origin_id and
            self.buyer_origin_id == other.buyer_origin_id and
            self.seller_id == other.seller_id and
            self.buyer_id == other.buyer_id
        )


class BalancingOffer(Offer):
    """BalancingOffer class."""

    def __repr__(self) -> str:
        return (f"<BalancingOffer('{self.id!s:.6s}', "
                f"'{self.energy} kWh@{self.price}', "
                f"'{self.seller} {self.energy_rate}'>")

    def __str__(self) -> str:
        return (f"<BalancingOffer{{{self.id!s:.6s}}} [{self.seller}]: "
                f"{self.energy} kWh @ {self.price} @ {self.energy_rate}>")


class BalancingTrade(Trade):
    """BalancingTrade class."""
    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [{self.seller} -> {self.buyer}] "
            f"{self.traded_energy} kWh @ {self.trade_price}"
            f" {self.trade_rate} {self.offer_bid.id}"
        )


@dataclass
class BidOfferMatch:
    """Representation of a market match."""
    market_id: str
    time_slot: str
    bid: Bid.serializable_dict
    selected_energy: float
    offer: Offer.serializable_dict
    trade_rate: float
    matching_requirements: Optional[Dict] = None

    def __post_init__(self):
        self.bid = deepcopy(self.bid)
        self.offer = deepcopy(self.offer)

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "market_id": self.market_id,
            "time_slot": self.time_slot,
            "bid": self.bid,
            "offer": self.offer,
            "selected_energy": self.selected_energy,
            "trade_rate": self.trade_rate,
            "matching_requirements": self.matching_requirements
        }

    @classmethod
    def from_dict(cls, bid_offer_match: Dict) -> Optional["BidOfferMatch"]:
        """Receive a serializable dict of BidOfferMatch and return a BidOfferMatch object."""
        if cls.is_valid_dict(bid_offer_match):
            return BidOfferMatch(**bid_offer_match)
        return None

    @classmethod
    def is_valid_dict(cls, bid_offer_match: Dict) -> bool:
        """Check whether a serialized dict can be a valid BidOfferMatch instance."""
        is_valid = True
        required_arguments = (
            "market_id", "time_slot", "bid", "offer", "selected_energy", "trade_rate")
        if not all(key in bid_offer_match for key in required_arguments):
            is_valid = False
        elif not isinstance(bid_offer_match["market_id"], str):
            is_valid = False
        elif not isinstance(bid_offer_match["selected_energy"], (int, float)):
            is_valid = False
        elif not isinstance(bid_offer_match["trade_rate"], (int, float)):
            is_valid = False
        elif not (bid_offer_match.get("matching_requirements") is None or
                  isinstance(bid_offer_match.get("matching_requirements"), Dict)):
            is_valid = False
        return is_valid

    @property
    def bid_energy(self):
        """
        Return the to-be considered bid's energy.

        A bid can have different energy requirements that are prioritized over its energy member.
        """
        if "bid_requirement" in (self.matching_requirements or {}):
            return (
                self.matching_requirements["bid_requirement"].get("energy")
                or self.bid["energy"])
        return self.bid["energy"]

    @property
    def bid_energy_rate(self):
        """
        Return the to-be considered bid's energy.

        A bid can have different energy requirements that are prioritized over its energy member.
        """
        if "bid_requirement" in (self.matching_requirements or {}):
            if "price" in self.matching_requirements["bid_requirement"]:
                return (
                    self.matching_requirements["bid_requirement"].get("price") /
                    self.bid_energy)
        return self.bid["energy_rate"]


@dataclass
class Clearing:
    """Class that contains information about the market clearing."""
    rate: float
    energy: float

    def serializable_dict(self):
        """Return a json serializable representation of the class."""
        return {
            "rate": self.rate,
            "energy": self.energy
        }


@dataclass
class MarketClearingState:
    """MarketClearingState class."""
    cumulative_offers: Dict[str, Dict[DateTime, Dict]] = field(default_factory=dict)
    cumulative_bids: Dict[str, Dict[DateTime, Dict]] = field(default_factory=dict)
    clearing: Dict[str, Dict[DateTime, Clearing]] = field(default_factory=dict)

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for CSV export."""
        return "creation_time", "rate [ct./kWh]"
