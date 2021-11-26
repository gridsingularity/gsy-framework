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
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=attribute-defined-outside-init

import json
import uuid
from copy import deepcopy
from dataclasses import asdict

import pytest
from pendulum import DateTime, datetime

from gsy_framework.data_classes import (
    OrdersMatch, BaseOrder, Offer, Bid, json_datetime_serializer,
    TradeOrdersInfo, Trade, BalancingOffer, BalancingTrade, Clearing,
    MarketClearingState)
from gsy_framework.utils import datetime_to_string_incl_seconds, limit_float_precision


DEFAULT_DATETIME = datetime(2021, 11, 3, 10, 45)


def test_json_datetime_serializer():
    """Test if json_datetime_serializer works as expected."""
    assert json_datetime_serializer("") is None

    my_date_time = DateTime.today()
    assert json_datetime_serializer(my_date_time) == datetime_to_string_incl_seconds(my_date_time)


class TestOrdersMatch:
    """Tester class for the OrdersMatch dataclass."""

    @staticmethod
    def test_serializable_dict():
        """Test the serializable_dict method of OrderMatch dataclass."""
        orders_match = OrdersMatch(
            market_id="market_id",
            time_slot="2021-10-06T12:00",
            bids=[{"type": "bid"}],
            offers=[{"type": "offer"}],
            selected_energy=1,
            trade_rate=1)
        expected_dict = {"market_id": "market_id",
                         "time_slot": "2021-10-06T12:00",
                         "bids": [{"type": "bid"}],
                         "offers": [{"type": "offer"}],
                         "selected_energy": 1,
                         "trade_rate": 1}
        assert orders_match.serializable_dict() == expected_dict

    @staticmethod
    def test_is_valid_dict():
        """Test the is_valid_dict method of OrderMatch dataclass."""
        orders_match = {"market_id": "market_id",
                        "time_slot": "2021-10-06T12:00",
                        "bids": [{"type": "bid"}],
                        "offers": [{"type": "offer"}],
                        "selected_energy": 1,
                        "trade_rate": 1}
        assert OrdersMatch.is_valid_dict(orders_match)

        # Key does not exist
        orders_match = {"market_id": "market_id",
                        "time_slot": "2021-10-06T12:00",
                        "bids": [{"type": "bid"}],
                        "offers": [{"type": "offer"}],
                        "selected_energy": 1,
                        }
        assert not OrdersMatch.is_valid_dict(orders_match)

        # Wrong type
        orders_match = {"market_id": "market_id",
                        "time_slot": "2021-10-06T12:00",
                        "bids": [{"type": "bid"}],
                        "offers": [{"type": "offer"}],
                        "selected_energy": 1,
                        "trade_rate": ""}
        assert not OrdersMatch.is_valid_dict(orders_match)

    @staticmethod
    def test_from_dict():
        """Test the from_dict method of OrderMatch dataclass."""
        expected_dict = {"market_id": "market_id",
                         "time_slot": "2021-10-06T12:00",
                         "bids": [{"type": "bid"}],
                         "offers": [{"type": "offer"}],
                         "selected_energy": 1,
                         "trade_rate": 1}
        orders_match = OrdersMatch.from_dict(expected_dict)
        assert orders_match.market_id == expected_dict["market_id"]
        assert orders_match.time_slot == expected_dict["time_slot"]
        assert orders_match.bids == expected_dict["bids"]
        assert orders_match.offers == expected_dict["offers"]
        assert orders_match.selected_energy == expected_dict["selected_energy"]
        assert orders_match.trade_rate == expected_dict["trade_rate"]


class TestBaseOrder:
    """Test BaseOrder class."""

    def setup_method(self):
        self.initial_data = {
            "id": str(uuid.uuid4()),
            "creation_time": DEFAULT_DATETIME,
            "time_slot": DEFAULT_DATETIME,
            "price": 10,
            "energy": 30,
            "original_price": 8,
            "attributes": {},
            "requirements": []
        }

    def test_init(self):
        """Test __init__."""
        orders = BaseOrder(
            **self.initial_data
        )
        assert orders.id == str(self.initial_data["id"])
        assert orders.creation_time == self.initial_data["creation_time"]
        assert orders.price == self.initial_data["price"]
        assert orders.energy == self.initial_data["energy"]
        assert orders.original_price == self.initial_data["original_price"]
        assert orders.energy_rate == limit_float_precision(self.initial_data["price"] /
                                                           self.initial_data["energy"])
        assert orders.attributes == self.initial_data["attributes"]
        assert orders.requirements == self.initial_data["requirements"]

        # Test whether the original_price will resort to the "price" member
        self.initial_data.pop("original_price")
        orders = BaseOrder(
            **self.initial_data
        )
        assert orders.original_price == self.initial_data["price"]

    def test_update_price(self):
        orders = BaseOrder(
            **self.initial_data
        )
        orders.update_price(30)
        assert orders.price == 30
        assert orders.energy_rate == 30 / orders.energy

    def test_update_energy(self):
        orders = BaseOrder(
            **self.initial_data
        )
        orders.update_energy(40)
        assert orders.energy == 40
        assert orders.energy_rate == orders.price / 40

    def test_to_json_string(self):
        orders = BaseOrder(
            **self.initial_data
        )
        obj_dict = deepcopy(orders.__dict__)

        obj_dict["type"] = "BaseOrder"
        assert orders.to_json_string() == json.dumps(obj_dict, default=json_datetime_serializer)
        assert json.loads(
            orders.to_json_string(my_extra_key=10)).get("my_extra_key") == 10

    def test_serializable_dict(self):
        orders = BaseOrder(
            **self.initial_data
        )
        assert orders.serializable_dict() == {
            "type": "BaseOrder",
            "id": str(orders.id),
            "energy": orders.energy,
            "energy_rate": orders.energy_rate,
            "original_price": orders.original_price,
            "creation_time": datetime_to_string_incl_seconds(orders.creation_time),
            "attributes": orders.attributes,
            "requirements": orders.requirements,
            "time_slot": datetime_to_string_incl_seconds(orders.time_slot)
        }

    def test_from_json(self):
        offer = Offer(
            **self.initial_data,
            seller="seller"
        )
        offer_json = offer.to_json_string()
        assert offer == BaseOrder.from_json(offer_json)

        bid = Bid(
            **self.initial_data,
            buyer="buyer"
        )
        bid_json = bid.to_json_string()
        assert bid == BaseOrder.from_json(bid_json)

    @pytest.mark.parametrize("time_stamp", [None, DEFAULT_DATETIME])
    def test_from_json_deals_with_time_stamps_correctly(self, time_stamp):
        updated_initial_data = self.initial_data
        updated_initial_data.update({"time_slot": time_stamp,
                                     "creation_time": time_stamp})
        bid = Bid(**updated_initial_data, buyer="buyer")
        bid_json = bid.to_json_string()
        bid = Bid.from_json(bid_json)
        assert bid.creation_time == time_stamp

    def test_from_json_asserts_if_no_type_was_provided(self):
        bid = Bid(**self.initial_data, buyer="buyer")
        bid_json = bid.to_json_string()
        bid_json = bid_json.replace(', "type": "Bid"', "")
        with pytest.raises(AssertionError):
            Bid.from_json(bid_json)

    def test_from_json_asserts_if_wrong_type_was_provided(self):
        bid = Bid(**self.initial_data, buyer="buyer")
        bid_json = bid.to_json_string()
        bid_json = bid_json.replace(', "type": "Bid"', ', "type": "InvalidType"')
        with pytest.raises(AssertionError):
            Bid.from_json(bid_json)


class TestOffer:
    def setup_method(self):
        self.initial_data = {
            "id": uuid.uuid4(),
            "creation_time": DEFAULT_DATETIME,
            "price": 10,
            "energy": 30,
            "original_price": 8,
            "attributes": {},
            "requirements": [],
            "seller": "seller",
            "time_slot": DEFAULT_DATETIME
        }

    def test_init(self):
        offer = Offer(
            **self.initial_data
        )
        assert offer.id == str(self.initial_data["id"])
        assert offer.creation_time == self.initial_data["creation_time"]
        assert offer.time_slot == self.initial_data["time_slot"]
        assert offer.price == self.initial_data["price"]
        assert offer.energy == self.initial_data["energy"]
        assert offer.original_price == self.initial_data["original_price"]
        assert offer.energy_rate == limit_float_precision(self.initial_data["price"] /
                                                          self.initial_data["energy"])
        assert offer.attributes == self.initial_data["attributes"]
        assert offer.requirements == self.initial_data["requirements"]
        assert offer.seller == "seller"
        assert offer.seller_id is None
        assert offer.seller_origin is None
        assert offer.seller_origin_id is None

    def test_hash(self):
        offer = Offer(
            **self.initial_data,
        )
        assert offer.__hash__() == hash(offer.id)

    def test_repr(self):
        offer = Offer(
            **self.initial_data,
        )
        assert (repr(offer) ==
                f"<Offer('{offer.id!s:.6s}', '{offer.energy} kWh@{offer.price}',"
                f" '{offer.seller} {offer.energy_rate}'>")

    def test_str(self):
        offer = Offer(
            **self.initial_data,
        )
        assert (str(offer) ==
                f"{{{offer.id!s:.6s}}} [origin: {offer.seller_origin}] "
                f"[{offer.seller}]: {offer.energy} kWh @ {offer.price} @ {offer.energy_rate}")

    def test_serializable_dict(self):
        offer = Offer(
            **self.initial_data,
        )
        assert offer.serializable_dict() == {
            "type": "Offer",
            "id": str(offer.id),
            "energy": offer.energy,
            "energy_rate": offer.energy_rate,
            "original_price": offer.original_price,
            "creation_time": datetime_to_string_incl_seconds(offer.creation_time),
            "attributes": offer.attributes,
            "requirements": offer.requirements,
            "seller": offer.seller,
            "seller_origin": offer.seller_origin,
            "seller_origin_id": offer.seller_origin_id,
            "seller_id": offer.seller_id,
            "time_slot": datetime_to_string_incl_seconds(offer.time_slot)
        }

    def test_from_dict(self):
        offer = Offer(
            **self.initial_data,
        )
        assert Offer.from_dict(offer.serializable_dict()) == offer

    def test_eq(self):
        offer = Offer(
            **self.initial_data
        )
        other_offer = Offer(
            **self.initial_data
        )
        assert offer == other_offer

        other_offer.id = "other_id"
        assert offer != other_offer

    def test_csv_values(self):
        offer = Offer(
            **self.initial_data
        )
        rate = round(offer.energy_rate, 4)
        assert offer.csv_values() == (
            offer.creation_time, rate, offer.energy, offer.price, offer.seller)

    @staticmethod
    def test_csv_fields():
        assert (Offer.csv_fields() ==
                ("creation_time", "rate [ct./kWh]", "energy [kWh]", "price [ct.]", "seller"))

    def test_copy(self):
        offer = Offer(
            **self.initial_data
        )
        second_offer = Offer.copy(offer)
        assert offer == second_offer


class TestBid:
    def setup_method(self):
        self.initial_data = {
            "id": uuid.uuid4(),
            "creation_time": DEFAULT_DATETIME,
            "price": 10,
            "energy": 30,
            "original_price": 8,
            "attributes": {},
            "requirements": [],
            "buyer": "buyer",
            "time_slot": DEFAULT_DATETIME
        }

    def test_init(self):
        bid = Bid(
            **self.initial_data
        )
        assert bid.id == str(self.initial_data["id"])
        assert bid.creation_time == self.initial_data["creation_time"]
        assert bid.price == self.initial_data["price"]
        assert bid.energy == self.initial_data["energy"]
        assert bid.original_price == self.initial_data["original_price"]
        assert bid.energy_rate == limit_float_precision(self.initial_data["price"] /
                                                        self.initial_data["energy"])
        assert bid.attributes == self.initial_data["attributes"]
        assert bid.requirements == self.initial_data["requirements"]
        assert bid.buyer == "buyer"
        assert bid.buyer_id is None
        assert bid.buyer_origin is None
        assert bid.buyer_origin_id is None

    def test_hash(self):
        bid = Bid(
            **self.initial_data
        )
        assert bid.__hash__() == hash(bid.id)

    def test_repr(self):
        bid = Bid(
            **self.initial_data
        )
        assert (repr(bid) ==
                f"<Bid {{{bid.id!s:.6s}}} [{bid.buyer}] "
                f"{bid.energy} kWh @ {bid.price} {bid.energy_rate}>")

    def test_str(self):
        bid = Bid(
            **self.initial_data
        )
        assert (str(bid) ==
                f"{{{bid.id!s:.6s}}} [origin: {bid.buyer_origin}] [{bid.buyer}] "
                f"{bid.energy} kWh @ {bid.price} {bid.energy_rate}")

    def test_serializable_dict(self):
        bid = Bid(
            **self.initial_data
        )

        assert bid.serializable_dict() == {
            "type": "Bid",
            "id": str(bid.id),
            "energy": bid.energy,
            "energy_rate": bid.energy_rate,
            "original_price": bid.original_price,
            "creation_time": datetime_to_string_incl_seconds(bid.creation_time),
            "attributes": bid.attributes,
            "requirements": bid.requirements,
            "buyer": bid.buyer,
            "buyer_origin": bid.buyer_origin,
            "buyer_origin_id": bid.buyer_origin_id,
            "buyer_id": bid.buyer_id,
            "time_slot": datetime_to_string_incl_seconds(bid.time_slot)
        }

    def test_from_dict(self):
        bid = Bid(
            **self.initial_data,
        )
        assert Bid.from_dict(bid.serializable_dict()) == bid

    def test_eq(self):
        bid = Bid(
            **self.initial_data
        )
        other_bid = Bid(
            **self.initial_data
        )
        assert bid == other_bid

        other_bid.id = "other_id"
        assert bid != other_bid

    def test_csv_values(self):
        bid = Bid(
            **self.initial_data
        )
        rate = round(bid.energy_rate, 4)
        assert bid.csv_values() == (bid.creation_time, rate, bid.energy, bid.price, bid.buyer)

    @staticmethod
    def test_csv_fields():
        assert (Bid.csv_fields() ==
                ("creation_time", "rate [ct./kWh]", "energy [kWh]", "price [ct.]", "buyer"))


class TestTradeOrdersInfo:
    @staticmethod
    def test_to_json_string():
        trade_orders_info = TradeOrdersInfo(
            1, 1, 1, 1, 1
        )
        assert (trade_orders_info.to_json_string() ==
                json.dumps(asdict(trade_orders_info), default=json_datetime_serializer))

    @staticmethod
    def test_from_json():
        trade_orders_info = TradeOrdersInfo(
            1, 1, 1, 1, 1
        )
        trade_orders_info_json = trade_orders_info.to_json_string()
        assert (TradeOrdersInfo.from_json(trade_orders_info_json) ==
                trade_orders_info)


class TestTrade:
    def setup_method(self):
        self.initial_data = {
            "id": "my_id",
            "creation_time": DEFAULT_DATETIME,
            "order": Offer("id", DEFAULT_DATETIME, 1, 2, "seller"),
            "seller": "seller",
            "buyer": "buyer"}

    def test_str(self):
        trade = Trade(**self.initial_data)
        assert (str(trade) ==
                f"{{{trade.id!s:.6s}}} [origin: {trade.seller_origin} -> {trade.buyer_origin}] "
                f"[{trade.seller} -> {trade.buyer}] {trade.order.energy} kWh"
                f" @ {trade.order.price} {round(trade.order.energy_rate, 8)} "
                f"{trade.order.id} [fee: {trade.fee_price} cts.]")

    @staticmethod
    def test_csv_fields():
        assert Trade.csv_fields() == (
            "creation_time", "rate [ct./kWh]", "energy [kWh]", "seller", "buyer")

    def test_csv_values(self):
        trade = Trade(**self.initial_data)
        rate = round(trade.order.energy_rate, 4)
        assert (trade.csv_values() ==
                (trade.creation_time, rate, trade.order.energy, trade.seller, trade.buyer))

    def test_to_json_string(self):
        trade = Trade(**self.initial_data)
        trade_dict = deepcopy(trade.__dict__)
        trade_dict["order"] = trade_dict["order"].to_json_string()
        assert (trade.to_json_string() ==
                json.dumps(trade_dict, default=json_datetime_serializer))

        # Test the residual check
        trade.residual = deepcopy(trade.order)
        trade_dict["residual"] = deepcopy(trade.order).to_json_string()
        assert (trade.to_json_string() ==
                json.dumps(trade_dict, default=json_datetime_serializer))
        assert json.loads(trade.to_json_string()).get("residual") is not None

        # Test the trade_orders_info check
        trade.trade_orders_info = TradeOrdersInfo(1, 2, 3, 4, 5)
        trade_dict["trade_orders_info"] = (
            deepcopy(trade.trade_orders_info).to_json_string())
        assert (trade.to_json_string() ==
                json.dumps(trade_dict, default=json_datetime_serializer))
        assert json.loads(trade.to_json_string()).get("trade_orders_info") is not None

    def test_from_json(self):
        trade = Trade(
            **self.initial_data
        )
        trade.residual = deepcopy(trade.order)
        trade.trade_orders_info = TradeOrdersInfo(
            1, 1, 1, 1, 1
        )
        assert Trade.from_json(trade.to_json_string()) == trade

    @pytest.mark.parametrize("time_stamp", [None, DEFAULT_DATETIME])
    def test_from_json_deals_with_time_stamps_correctly(self, time_stamp):
        updated_initial_data = self.initial_data
        updated_initial_data.update({"time_slot": time_stamp,
                                     "creation_time": time_stamp})
        trade = Trade(**updated_initial_data)
        trade_json = trade.to_json_string()
        trade = Trade.from_json(trade_json)
        assert trade.creation_time == time_stamp

    def test_is_bid_trade(self):
        trade = Trade(
            **self.initial_data
        )
        assert trade.is_bid_trade is False

        trade.order = Bid("id", DateTime.now(), 1, 2, "buyer")
        assert trade.is_bid_trade is True

    def test_is_offer_trade(self):
        trade = Trade(
            **self.initial_data
        )
        assert trade.is_offer_trade is True

        trade.order = Bid("id", DateTime.now(), 1, 2, "buyer")
        assert trade.is_offer_trade is False

    @staticmethod
    def test_serializable_dict():
        trade = Trade(
            **{
                "id": "my_id",
                "order": Offer("id", DEFAULT_DATETIME, 1, 2, "seller"),
                "buyer": "buyer",
                "buyer_origin": "buyer_origin",
                "seller_origin": "seller_origin",
                "seller_origin_id": "seller_origin_id",
                "buyer_origin_id": "buyer_origin_id",
                "seller_id": "seller_id",
                "buyer_id": "buyer_id",
                "seller": "seller",
                "fee_price": 2,
                "creation_time": DEFAULT_DATETIME,
                "time_slot": DEFAULT_DATETIME
            }
        )
        assert trade.serializable_dict() == {
            "type": "Trade",
            "match_type": "Offer",
            "id": trade.id,
            "order_id": trade.order.id,
            "residual_id": trade.residual.id if trade.residual is not None else None,
            "energy": trade.order.energy,
            "energy_rate": trade.order.energy_rate,
            "price": trade.order.price,
            "buyer": trade.buyer,
            "buyer_origin": trade.buyer_origin,
            "seller_origin": trade.seller_origin,
            "seller_origin_id": trade.seller_origin_id,
            "buyer_origin_id": trade.buyer_origin_id,
            "seller_id": trade.seller_id,
            "buyer_id": trade.buyer_id,
            "seller": trade.seller,
            "fee_price": trade.fee_price,
            "creation_time": datetime_to_string_incl_seconds(trade.creation_time),
            "time_slot": datetime_to_string_incl_seconds(trade.creation_time)
        }


class TestBalancingOffer(TestOffer):
    def setup_method(self):
        self.initial_data = {
            "id": uuid.uuid4(),
            "creation_time": DEFAULT_DATETIME,
            "price": 10,
            "energy": 30,
            "original_price": 8,
            "attributes": {},
            "requirements": [],
            "seller": "seller",
            "time_slot": DEFAULT_DATETIME
        }

    def test_repr(self):
        offer = BalancingOffer(**self.initial_data)
        assert (repr(offer) ==
                f"<BalancingOffer('{offer.id!s:.6s}', "
                f"'{offer.energy} kWh@{offer.price}', "
                f"'{offer.seller} {offer.energy_rate}'>")

    def test_str(self):
        offer = BalancingOffer(**self.initial_data)
        assert (str(offer) ==
                f"<BalancingOffer{{{offer.id!s:.6s}}} [{offer.seller}]: "
                f"{offer.energy} kWh @ {offer.price} @ {offer.energy_rate}>")


class TestBalancingTrade(TestTrade):

    def test_str(self):
        trade = BalancingTrade(**self.initial_data)
        assert (str(trade) ==
                f"{{{trade.id!s:.6s}}} [{trade.seller} -> {trade.buyer}] "
                f"{trade.order.energy} kWh @ {trade.order.price}"
                f" {trade.order.energy_rate} {trade.order.id}")


class TestClearing:
    @staticmethod
    def test_serializable_dict():
        clearing = Clearing(energy=1, rate=1)
        assert clearing.serializable_dict() == {
            "energy": 1, "rate": 1}


class TestMarketClearingState:
    @staticmethod
    def test_csv_fields():
        assert MarketClearingState.csv_fields() == ("creation_time", "rate [ct./kWh]")
