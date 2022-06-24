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

from tests.test_matching_algorithms import offer_factory, bid_factory
from gsy_framework.data_classes import BidOfferMatch
from gsy_framework.matching_algorithms.attributed_matching_algorithm import (
    AttributedMatchingAlgorithm)


class TestAttributedMatchingAlgorithm:
    """Tester class for the PreferredPartnersMatchingAlgorithm."""

    @staticmethod
    def test_get_matches_recommendations_respects_trading_partners():
        """Test the main interface of the algorithm.
         Pass supported format data and receive correct results
         """
        offer = offer_factory().serializable_dict()
        bid = bid_factory(
            {"requirements": [{"trading_partners": [offer["seller_id"]]}]}
        ).serializable_dict()

        offer2 = offer_factory(
            {"seller_id": "second seller", "seller_origin_id": "second seller"}
        ).serializable_dict()
        # Both the seller and seller_origin ids are used for preferred trading partner matching.
        bid2 = bid_factory().serializable_dict()
        data = {"market": {"2021-10-06T12:00": {
            "bids": [bid, bid2], "offers": [offer, offer2]
        }}}

        matches = AttributedMatchingAlgorithm.get_matches_recommendations(data)
        assert matches[0]["offer"]["id"] == offer["id"]
        assert matches[0]["bid"]["id"] == bid["id"]

        assert matches[0] == BidOfferMatch(
            bid=bid, offer=offer,
            market_id="market",
            trade_rate=bid["energy_rate"],
            selected_energy=30,
            time_slot="2021-10-06T12:00",
            matching_requirements={
               "bid_requirement": {"trading_partners": [offer["seller_id"]]},
               "offer_requirement": {}}).serializable_dict()

        assert matches[1]["offer"]["id"] == offer2["id"]
        assert matches[1]["bid"]["id"] == bid2["id"]
        assert matches[1] == BidOfferMatch(
            bid=bid2, offer=offer2,
            market_id="market",
            trade_rate=bid2["energy_rate"],
            selected_energy=30,
            time_slot="2021-10-06T12:00",
            matching_requirements=None).serializable_dict()

    @staticmethod
    def test_get_matches_recommendations_respects_green_energy():
        """Test the main interface of the algorithm.
         Pass supported format data and receive correct results
         """
        offer = offer_factory({"attributes": {"energy_type": "PV"}}).serializable_dict()
        bid = bid_factory(
            {"requirements": [{"energy_type": ["PV"]}]}
        ).serializable_dict()

        offer2 = offer_factory().serializable_dict()
        bid2 = bid_factory().serializable_dict()
        data = {"market": {"2021-10-06T12:00": {
            "bids": [bid, bid2], "offers": [offer, offer2]
        }}}

        matches = AttributedMatchingAlgorithm.get_matches_recommendations(data)
        assert matches[0]["offer"]["id"] == offer["id"]
        assert matches[0]["bid"]["id"] == bid["id"]

        assert matches[0] == BidOfferMatch(
            bid=bid, offer=offer,
            market_id="market",
            trade_rate=bid["energy_rate"],
            selected_energy=30,
            time_slot="2021-10-06T12:00",
            matching_requirements={
               "bid_requirement": {"energy_type": ["PV"]},
               "offer_requirement": {}}).serializable_dict()

        assert matches[1]["offer"]["id"] == offer2["id"]
        assert matches[1]["bid"]["id"] == bid2["id"]
        assert matches[1] == BidOfferMatch(
            bid=bid2, offer=offer2,
            market_id="market",
            trade_rate=bid2["energy_rate"],
            selected_energy=30,
            time_slot="2021-10-06T12:00",
            matching_requirements=None).serializable_dict()
