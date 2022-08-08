"""
Copyright 2018 Grid Singularity
This file is part of GSy Interface.

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
# pylint: disable=protected-access

from gsy_framework.data_classes import BidOfferMatch
from gsy_framework.matching_algorithms.preferred_partners_algorithm import (
    PreferredPartnersMatchingAlgorithm)
from tests.test_matching_algorithms import offer_factory, bid_factory


class TestPreferredPartnersMatchingAlgorithm:
    """Tester class for the PreferredPartnersMatchingAlgorithm."""

    @staticmethod
    def test_get_matches_recommendations():
        """Test the main interface of the algorithm.
         Pass supported format data and receive correct results
         """
        offer = offer_factory().serializable_dict()
        bid = bid_factory(
            {"requirements": [{"trading_partners": [offer["seller_id"]]}]}
        ).serializable_dict()
        data = {"market": {"2021-10-06T12:00": {
            "bids": [bid], "offers": [offer]
        }}}
        assert PreferredPartnersMatchingAlgorithm.get_matches_recommendations(
            data) == [
                   BidOfferMatch(bid=bid, offer=offer,
                                 market_id="market",
                                 trade_rate=bid["energy_rate"],
                                 selected_energy=30,
                                 time_slot="2021-10-06T12:00",
                                 matching_requirements={
                                     "bid_requirement": {"trading_partners": [offer["seller_id"]]},
                                     "offer_requirement": {}
                                 }).serializable_dict()]

    @staticmethod
    def test_get_energy_and_clearing_rate():
        offer = offer_factory().serializable_dict()
        assert PreferredPartnersMatchingAlgorithm._get_required_energy_and_rate_from_order(
            order=offer, order_requirement={}
        ) == (offer["energy"], offer["energy_rate"])

        order_requirement = {"energy": 10, "price": 1}
        assert PreferredPartnersMatchingAlgorithm._get_required_energy_and_rate_from_order(
            order=offer, order_requirement=order_requirement) == (
            order_requirement["energy"], order_requirement["price"] / order_requirement["energy"])

    @staticmethod
    def test_get_actors_mapping():
        offers = [
            offer_factory({
                "id": f"id-{index}",
                "seller_id": f"seller_id-{index}",
                "seller": f"seller-{index}",
                "seller_origin_id": f"seller_id-{index}",
                "seller_origin": f"seller-{index}"}).serializable_dict()
            for index in range(3)]
        offers.append(offer_factory({
            "seller_id": offers[0]["seller_id"],
            "seller_origin_id": "different_origin_id",
            "seller_origin": "different_origin"}).serializable_dict())
        assert PreferredPartnersMatchingAlgorithm._get_actor_to_offers_mapping(offers) == {
            "seller_id-0": [offers[0], offers[3]],
            "seller_id-1": [offers[1]],
            "seller_id-2": [offers[2]],
            "different_origin_id": [offers[3]]}

    @staticmethod
    def test_can_order_be_matched():
        bid = bid_factory(
            {"requirements": [{"energy_type": ["green"]}]}).serializable_dict()
        offer = offer_factory().serializable_dict()
        assert PreferredPartnersMatchingAlgorithm._can_order_be_matched(
            bid=bid,
            offer=offer,
            bid_requirement=bid["requirements"][0],
            offer_requirement={}) is False

        offer["attributes"] = {"energy_type": "green"}
        assert PreferredPartnersMatchingAlgorithm._can_order_be_matched(
            bid=bid,
            offer=offer,
            bid_requirement=bid["requirements"][0],
            offer_requirement={}) is True

        offer["energy_rate"] = bid["energy_rate"] + 0.1
        assert PreferredPartnersMatchingAlgorithm._can_order_be_matched(
            bid=bid,
            offer=offer,
            bid_requirement=bid["requirements"][0],
            offer_requirement={}) is False
