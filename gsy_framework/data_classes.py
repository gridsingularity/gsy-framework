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
from math import isclose
from typing import Dict, Optional, Tuple, Union
from decimal import Decimal
from pendulum import DateTime

from gsy_framework.constants_limits import (
    DEFAULT_PRECISION,
    FLOATING_POINT_TOLERANCE,
    ENERGY_RATE_PRECISION,
)
from gsy_framework.utils import datetime_to_string_incl_seconds, str_to_pendulum_datetime


def json_datetime_serializer(datetime_obj: DateTime) -> Optional[str]:
    """Define how to convert datetime objects while serializing to json."""
    if isinstance(datetime_obj, DateTime):
        return datetime_to_string_incl_seconds(datetime_obj)
    return None


class BaseBidOffer:
    """Base class defining shared functionality of Bid and Offer market structures."""

    def __init__(
        self,
        id: str,
        creation_time: DateTime,
        price: float,
        energy: float,
        original_price: Optional[float] = None,
        time_slot: DateTime = None,
    ):
        self.id = str(id)
        self.creation_time = creation_time
        self.time_slot = time_slot  # market slot of creation
        self.original_price = original_price or price
        self.price = price
        self.energy = energy
        self.type = self.__class__.__name__

    @property
    def energy_rate(self) -> float:
        """Dynamically calculate rate of energy."""
        return round(self.price / self.energy, ENERGY_RATE_PRECISION)

    @property
    def original_energy_rate(self) -> float:
        """Dynamically calculate energy rate of original order."""
        return round(self.original_price / self.energy, ENERGY_RATE_PRECISION)

    def update_price(self, price: float) -> None:
        """Update price member."""
        self.price = price

    def update_energy(self, energy: float) -> None:
        """Update energy member."""
        self.energy = energy

    def to_json_string(self) -> str:
        """Convert the Offer or Bid object into its JSON representation."""
        return json.dumps(self.serializable_dict(), default=json_datetime_serializer)

    @classmethod
    def from_dict(cls, order: Dict) -> Union["Bid", "Offer"]:
        """Deserialize an offer or bid dict."""
        return cls.from_serializable_dict(order)

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "type": self.type,
            "id": self.id,
            "energy": self.energy,
            "energy_rate": self.energy_rate,
            "price": self.price,
            "original_price": self.original_price,
            "creation_time": datetime_to_string_incl_seconds(self.creation_time),
            "time_slot": datetime_to_string_incl_seconds(self.time_slot),
        }

    @classmethod
    def from_json(cls, offer_or_bid: Union[str, Dict]) -> Union["Offer", "Bid"]:
        """De-serialize orders from json string."""
        if isinstance(offer_or_bid, str):
            return cls.from_serializable_dict(json.loads(offer_or_bid))
        return cls.from_serializable_dict(offer_or_bid)

    @classmethod
    def from_serializable_dict(cls, offer_bid_dict: Dict) -> Union["Offer", "Bid"]:
        """Construct Offer / Bid objects from a serializable dict."""
        order_dict_copy = deepcopy(offer_bid_dict)
        object_type = order_dict_copy.pop("type", None)
        if not object_type:
            assert False, "from_json expects a json string containing the 'type' key"
        order_dict_copy.pop("energy_rate", None)
        order_dict_copy["creation_time"] = (
            str_to_pendulum_datetime(order_dict_copy["creation_time"])
            if order_dict_copy.get("creation_time")
            else None
        )

        order_dict_copy["time_slot"] = (
            str_to_pendulum_datetime(order_dict_copy["time_slot"])
            if order_dict_copy.get("time_slot")
            else None
        )

        if order_dict_copy.get("seller"):
            order_dict_copy["seller"] = TraderDetails.from_serializable_dict(
                order_dict_copy["seller"]
            )
        if order_dict_copy.get("buyer"):
            order_dict_copy["buyer"] = TraderDetails.from_serializable_dict(
                order_dict_copy["buyer"]
            )

        if object_type == "Offer":
            return Offer(**order_dict_copy)
        if object_type == "Bid":
            return Bid(**order_dict_copy)
        assert False, "the type member needs to be set to one of ('Bid', 'Offer')."

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the order."""
        return 0


@dataclass(frozen=True)
class TraderDetails:
    """
    Details about the trader. Includes trader name and unique identifier, and also the original
    trader for this order.
    """

    name: str
    uuid: str
    origin: Optional[str] = None
    origin_uuid: Optional[str] = None

    def __eq__(self, other: "TraderDetails") -> bool:
        return (
            self.name == other.name
            and self.origin == other.origin
            and self.uuid == other.uuid
            and self.origin_uuid == other.origin_uuid
        )

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "name": self.name,
            "origin": self.origin,
            "origin_uuid": self.origin_uuid,
            "uuid": self.uuid,
        }

    @staticmethod
    def from_serializable_dict(trader_details: Dict) -> "TraderDetails":
        """Get a TraderDetails object from a serializable dictionary."""
        return TraderDetails(**trader_details)


class Offer(BaseBidOffer):
    """Offer class"""

    def __init__(
        self,
        id: str,
        creation_time: DateTime,
        price: float,
        energy: float,
        seller: TraderDetails,
        original_price: Optional[float] = None,
        time_slot: DateTime = None,
    ):
        super().__init__(
            id=id,
            creation_time=creation_time,
            price=price,
            energy=energy,
            original_price=original_price,
            time_slot=time_slot,
        )
        self.seller = seller

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"<Offer('{self.id!s:.6s}', '{self.energy} kWh@{self.price}',"
            f" '{self.seller.name} {self.energy_rate}'>"
        )

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [origin: {self.seller.origin}] "
            f"[{self.seller.name}]: {self.energy} kWh @ {self.price} "
            f"@ {self.energy_rate}"
        )

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {**super().serializable_dict(), "seller": self.seller.serializable_dict()}

    def __eq__(self, other: "Offer") -> bool:
        return (
            self.id == other.id
            and isclose(self.energy_rate, other.energy_rate, rel_tol=FLOATING_POINT_TOLERANCE)
            and isclose(self.energy, other.energy, rel_tol=FLOATING_POINT_TOLERANCE)
            and isclose(self.price, other.price, rel_tol=FLOATING_POINT_TOLERANCE)
            and self.seller == other.seller
            and self.creation_time == other.creation_time
            and self.time_slot == other.time_slot
        )

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.energy_rate, 4)
        return (
            self.creation_time,
            rate,
            self.energy,
            self.price,
            self.seller.name,
            self.seller.origin,
        )

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return (
            "creation_time",
            "rate [ct./kWh]",
            "energy [kWh]",
            "price [ct.]",
            "seller",
            "seller origin",
        )

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the offer."""
        return self.price - self.original_price

    @staticmethod
    def copy(offer: "Offer") -> "Offer":
        """Return a copy of an offer Object."""
        return Offer(
            offer.id,
            offer.creation_time,
            offer.price,
            offer.energy,
            seller=offer.seller,
            original_price=offer.original_price,
            time_slot=offer.time_slot,
        )


class Bid(BaseBidOffer):
    """Bid class."""

    def __init__(
        self,
        id: str,
        creation_time: DateTime,
        price: float,
        energy: float,
        buyer: TraderDetails,
        original_price: Optional[float] = None,
        time_slot: Optional[DateTime] = None,
    ):
        super().__init__(
            id=id,
            creation_time=creation_time,
            price=price,
            energy=energy,
            original_price=original_price,
            time_slot=time_slot,
        )
        self.buyer = buyer

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"<Bid {{{self.id!s:.6s}}} [{self.buyer.name}] "
            f"{self.energy} kWh @ {self.price} {self.energy_rate}>"
        )

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [origin: {self.buyer.origin}] [{self.buyer.name}] "
            f"{self.energy} kWh @ {self.price} {self.energy_rate}"
        )

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {**super().serializable_dict(), "buyer": self.buyer.serializable_dict()}

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.energy_rate, 4)
        return (
            self.creation_time,
            rate,
            self.energy,
            self.price,
            self.buyer.name,
            self.buyer.origin,
        )

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return (
            "creation_time",
            "rate [ct./kWh]",
            "energy [kWh]",
            "price [ct.]",
            "buyer",
            "buyer origin",
        )

    @property
    def accumulated_grid_fees(self):
        """Return the accumulated grid fees alongside the path of the bid."""
        return self.original_price - self.price

    def __eq__(self, other: "Bid") -> bool:
        return (
            self.id == other.id
            and self.buyer == other.buyer
            and self.creation_time == other.creation_time
            and self.time_slot == other.time_slot
        )


@dataclass
class TradeBidOfferInfo:
    """Class that contains information about the original bid or offer."""

    original_bid_rate: Optional[float]
    propagated_bid_rate: Optional[float]
    original_offer_rate: Optional[float]
    propagated_offer_rate: Optional[float]
    trade_rate: Optional[float]

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return asdict(self)

    def to_json_string(self) -> str:
        """Return json string of the representation."""
        return json.dumps(self.serializable_dict(), default=json_datetime_serializer)

    @staticmethod
    def from_json(trade_bid_offer_info: Union[str, Dict]) -> "TradeBidOfferInfo":
        """Return TradeBidOfferInfo object from json representation."""
        if isinstance(trade_bid_offer_info, str):
            info_dict = json.loads(trade_bid_offer_info)
            return TradeBidOfferInfo(**info_dict)
        return TradeBidOfferInfo(**trade_bid_offer_info)

    def __eq__(self, other: "TradeBidOfferInfo") -> bool:
        return (
            self.original_offer_rate == other.original_offer_rate
            and self.original_bid_rate == other.original_bid_rate
            and self.propagated_bid_rate == other.propagated_bid_rate
            and self.propagated_offer_rate == other.propagated_offer_rate
            and self.trade_rate == self.trade_rate
        )


class Trade:
    """Trade class."""

    def __init__(
        self,
        id: str,
        creation_time: DateTime,
        seller: TraderDetails,
        buyer: TraderDetails,
        traded_energy: float,
        trade_price: float,
        offer: Offer = None,
        bid: Bid = None,
        residual: Optional[Union[Offer, Bid]] = None,
        offer_bid_trade_info: Optional[TradeBidOfferInfo] = None,
        fee_price: Optional[float] = None,
        time_slot: Optional[DateTime] = None,
        matching_requirements: Optional[Dict] = None,
    ):

        self.id = str(id)
        self.creation_time = creation_time
        self.time_slot = time_slot  # market slot of creation
        self.traded_energy = traded_energy
        self.trade_price = trade_price
        self.residual = residual
        self.offer_bid_trade_info = offer_bid_trade_info
        self.fee_price = fee_price
        self.seller = seller
        self.buyer = buyer
        self.matching_requirements = matching_requirements
        self.match_details = {"offer": offer, "bid": bid}

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} "
            f"[origin: {self.seller.origin} -> "
            f"{self.buyer.origin}] "
            f"[{self.seller.name} -> {self.buyer.name}] "
            f"{self.traded_energy} kWh @ {self.trade_price} {round(self.trade_rate, 8)} "
            f"{self.match_details['offer'].id if self.match_details['offer'] else ''} "
            f"{self.match_details['bid'].id if self.match_details['bid'] else ''} "
            f"[fee: {self.fee_price} cts.] "
            f"{self.matching_requirements or ''}"
        )

    @classmethod
    def csv_fields(cls) -> Tuple:
        """Return labels for csv_values for CSV export."""
        return (
            "creation_time",
            "rate [ct./kWh]",
            "energy [kWh]",
            "seller",
            "seller origin",
            "buyer",
            "buyer origin",
        )

    def csv_values(self) -> Tuple:
        """Return values of class members that are needed for creation of CSV export."""
        rate = round(self.trade_rate, 4)
        return (
            self.creation_time,
            rate,
            self.traded_energy,
            self.seller.name,
            self.seller.origin,
            self.buyer.name,
            self.buyer.origin,
        )

    def to_json_string(self) -> str:
        """Return json string of the representation."""
        return json.dumps(self.serializable_dict())

    @classmethod
    def from_json(cls, trade_string) -> "Trade":
        """De-serialize trade from json string."""
        return cls.from_dict(json.loads(trade_string))

    @classmethod
    def from_dict(cls, trade_dict: Dict) -> "Trade":
        """
        Create Trade object from a dict that contains nested unserializable structs
        (including offer, bid, residual and datetimes).
        """
        trade_dict["offer"] = (
            BaseBidOffer.from_json(trade_dict["offer"]) if trade_dict.get("offer") else None
        )
        trade_dict["bid"] = (
            BaseBidOffer.from_json(trade_dict["bid"]) if trade_dict.get("bid") else None
        )
        trade_dict["residual"] = (
            BaseBidOffer.from_json(trade_dict["residual"]) if trade_dict.get("residual") else None
        )

        trade_dict["creation_time"] = (
            str_to_pendulum_datetime(trade_dict["creation_time"])
            if trade_dict.get("creation_time")
            else None
        )

        trade_dict["time_slot"] = (
            str_to_pendulum_datetime(trade_dict["time_slot"])
            if trade_dict.get("time_slot")
            else None
        )

        trade_dict["offer_bid_trade_info"] = (
            TradeBidOfferInfo.from_json(trade_dict["offer_bid_trade_info"])
            if trade_dict.get("offer_bid_trade_info")
            else None
        )

        if trade_dict["seller"] is not None:
            trade_dict["seller"] = TraderDetails.from_serializable_dict(trade_dict["seller"])
        if trade_dict["buyer"] is not None:
            trade_dict["buyer"] = TraderDetails.from_serializable_dict(trade_dict["buyer"])

        return cls.from_serializable_dict(trade_dict)

    @property
    def is_bid_trade(self) -> bool:
        """Check if the instance is a bid trade."""
        return self.match_details["bid"] is not None

    @property
    def is_offer_trade(self) -> bool:
        """Check if the instance is an offer trade."""
        return self.match_details["offer"] is not None

    @property
    def trade_rate(self):
        """Return the energy rate of the trade."""
        return round(self.trade_price / self.traded_energy, DEFAULT_PRECISION)

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {
            "type": "Trade",
            "match_type": ("Bid" if self.is_bid_trade else "Offer"),
            "id": self.id,
            "bid": (
                self.match_details["bid"].serializable_dict()
                if self.match_details.get("bid")
                else None
            ),
            "offer": (
                self.match_details["offer"].serializable_dict()
                if self.match_details.get("offer")
                else None
            ),
            "residual": self.residual.serializable_dict() if self.residual is not None else None,
            "energy": self.traded_energy,
            "energy_rate": self.trade_rate,
            "price": self.trade_price,
            "buyer": self.buyer.serializable_dict(),
            "seller": self.seller.serializable_dict(),
            "fee_price": self.fee_price,
            "creation_time": datetime_to_string_incl_seconds(self.creation_time),
            "time_slot": datetime_to_string_incl_seconds(self.time_slot),
            "offer_bid_trade_info": (
                self.offer_bid_trade_info.serializable_dict()
                if self.offer_bid_trade_info
                else None
            ),
        }

    @classmethod
    def from_serializable_dict(cls, trade_dict: Dict) -> "Trade":
        """Return a Trade object parsed from trade_dict."""
        return Trade(
            id=trade_dict["id"],
            creation_time=trade_dict["creation_time"],
            seller=trade_dict["seller"],
            buyer=trade_dict["buyer"],
            traded_energy=trade_dict["energy"],
            trade_price=trade_dict["price"],
            offer=trade_dict["offer"],
            bid=trade_dict["bid"],
            offer_bid_trade_info=trade_dict.get("offer_bid_trade_info"),
            residual=trade_dict.get("residual"),
            time_slot=trade_dict["time_slot"],
        )

    def __eq__(self, other: "Trade") -> bool:
        return (
            self.id == other.id
            and self.creation_time == other.creation_time
            and self.time_slot == other.time_slot
            and self.match_details["offer"] == other.match_details["offer"]
            and self.match_details["bid"] == other.match_details["bid"]
            and self.seller == other.seller
            and self.buyer == other.buyer
            and self.traded_energy == other.traded_energy
            and self.trade_price == other.trade_price
            and self.residual == other.residual
            and self.offer_bid_trade_info == other.offer_bid_trade_info
        )


class BalancingOffer(Offer):
    """BalancingOffer class."""

    def __repr__(self) -> str:
        return (
            f"<BalancingOffer('{self.id!s:.6s}', "
            f"'{self.energy} kWh@{self.price}', "
            f"'{self.seller.name} {self.energy_rate}'>"
        )

    def __str__(self) -> str:
        return (
            f"<BalancingOffer{{{self.id!s:.6s}}} [{self.seller.name}]: "
            f"{self.energy} kWh @ {self.price} @ {self.energy_rate}>"
        )


class BalancingTrade(Trade):
    """BalancingTrade class."""

    def __str__(self) -> str:
        return (
            f"{{{self.id!s:.6s}}} [{self.seller.name} -> {self.buyer.name}] "
            f"{self.traded_energy} kWh @ {self.trade_price}"
            f" {self.trade_rate} "
            f"{self.match_details['offer'].id if self.match_details['offer'] else ''} "
            f"{self.match_details['bid'].id if self.match_details['bid'] else ''} "
        )


@dataclass
class BidOfferMatch:
    """Representation of a market match."""

    market_id: str
    time_slot: str
    bid: Bid.serializable_dict
    selected_energy: Decimal
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
            "selected_energy": float(self.selected_energy),
            "trade_rate": self.trade_rate,
            "matching_requirements": self.matching_requirements,
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
            "market_id",
            "time_slot",
            "bid",
            "offer",
            "selected_energy",
            "trade_rate",
        )
        if not all(key in bid_offer_match for key in required_arguments):
            is_valid = False
        elif not isinstance(bid_offer_match["market_id"], str):
            is_valid = False
        elif not isinstance(bid_offer_match["selected_energy"], (int, float, Decimal)):
            is_valid = False
        elif not isinstance(bid_offer_match["trade_rate"], (int, float)):
            is_valid = False
        elif not (
            bid_offer_match.get("matching_requirements") is None
            or isinstance(bid_offer_match.get("matching_requirements"), Dict)
        ):
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
                self.matching_requirements["bid_requirement"].get("energy") or self.bid["energy"]
            )
        return self.bid["energy"]

    @property
    def bid_energy_rate(self):
        """
        Return the to-be considered bid's energy.

        A bid can have different energy requirements that are prioritized over its energy member.
        """
        if "bid_requirement" in (self.matching_requirements or {}):
            if "price" in self.matching_requirements["bid_requirement"]:
                return self.matching_requirements["bid_requirement"].get("price") / self.bid_energy
        return self.bid["energy_rate"]


@dataclass
class Clearing:
    """Class that contains information about the market clearing."""

    rate: float
    energy: float

    def serializable_dict(self):
        """Return a json serializable representation of the class."""
        return {"rate": self.rate, "energy": self.energy}


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
