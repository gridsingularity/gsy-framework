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
from collections import namedtuple
from typing import List, Dict
from uuid import uuid4

import pendulum
import pytest

from d3a_interface.constants_limits import FLOATING_POINT_TOLERANCE
from d3a_interface.data_classes import Clearing
from d3a_interface.matching_algorithms import PayAsClearMatchingAlgorithm

Offer = namedtuple("Offer", ["id", "time", "price", "energy", "seller"])
Bid = namedtuple("Bid", ["id", "time", "price", "energy", "buyer"])


class TestPayAsClearMatchingAlgorithm:

    @staticmethod
    def validate_matching(
            matching: Dict, matched_energy: float,
            offer_id: str, bid_id: str) -> None:
        """Validate if a BidOfferMatch dict is valid.

        Raises:
            AssertionError
        """
        assert matching["selected_energy"] == matched_energy
        assert len(matching["offers"]) == 1
        assert len(matching["bids"]) == 1
        assert matching["offers"][0]["id"] == offer_id
        assert matching["bids"][0]["id"] == bid_id

    @pytest.mark.parametrize(
        "energy_values,clearing_energy", [
            ([1, 2, 3, 4, 5], 15),
            ([5, 4, 3, 2, 1], 15),
            ([12, 123, 432, 543, 1], 1111.2),
            ([867867.61, 123.98, 432.43, 12.12, 0.001], 868440)
        ])
    def test_create_bid_offer_matches_respects_offer_bid_order(
            self, energy_values: List[float], clearing_energy: float) -> None:
        bids_list = []
        offers_list = []
        for index, energy in enumerate(energy_values):
            bids_list.append(
                Bid(f"bid_id{index}", pendulum.now(), index, energy, "Buyer")._asdict())
            offers_list.append(
                Offer(f"offer_id{index}", pendulum.now(), index, energy, "Seller")._asdict())
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        current_time = str(pendulum.now())
        timeslot = "2021-10-06T12:00"
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, clearing_energy)}
        matches = pac_algo._create_bid_offer_matches(
            offers_list, bids_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)
        assert len(matches) == 5
        for index in range(5):
            self.validate_matching(
                matches[index], energy_values[index], f"offer_id{index}", f"bid_id{index}")

    def test_create_bid_offer_matches_can_handle_partial_bids(self):
        bids_list = [
            Bid("bid_id1", pendulum.now(), 9, 9, "Buyer")._asdict(),
            Bid("bid_id2", pendulum.now(), 3, 3, "Buyer")._asdict(),
            Bid("bid_id3", pendulum.now(), 3, 3, "Buyer")._asdict(),
        ]

        offers_list = []
        for index in range(1, 6):
            offers_list.append(
                Offer(f"offer_id{index}", pendulum.now(), index, index, "Seller")._asdict())
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        current_time = str(pendulum.now())
        timeslot = "2021-10-06T12:00"
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offers_list, bids_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        assert len(matches) == 7
        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id2", "bid_id1")
        self.validate_matching(matches[2], 3, "offer_id3", "bid_id1")
        self.validate_matching(matches[3], 3, "offer_id4", "bid_id1")
        self.validate_matching(matches[4], 1, "offer_id4", "bid_id2")
        self.validate_matching(matches[5], 2, "offer_id5", "bid_id2")
        self.validate_matching(matches[6], 3, "offer_id5", "bid_id3")

    def test_create_bid_offer_matches_can_handle_partial_offers(self):
        bid_list = []
        for index in range(1, 6):
            bid_list.append(
                Bid(f"bid_id{index}", pendulum.now(), index, index, "B")._asdict()
            )

        offer_list = [
            Offer("offer_id1", pendulum.now(), 8, 8, "S")._asdict(),
            Offer("offer_id2", pendulum.now(), 4, 4, "S")._asdict(),
            Offer("offer_id3", pendulum.now(), 3, 3, "S")._asdict(),
        ]
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        timeslot = "2021-10-06T12:00"
        current_time = str(pendulum.now())
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offer_list, bid_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id1", "bid_id2")
        self.validate_matching(matches[2], 3, "offer_id1", "bid_id3")
        self.validate_matching(matches[3], 2, "offer_id1", "bid_id4")
        self.validate_matching(matches[4], 2, "offer_id2", "bid_id4")
        self.validate_matching(matches[5], 2, "offer_id2", "bid_id5")
        self.validate_matching(matches[6], 3, "offer_id3", "bid_id5")

    def test_create_bid_offer_matches_can_handle_excessive_offer_energy(self):
        bid_list = []
        for index in range(1, 6):
            bid_list.append(
                Bid(f"bid_id{index}", pendulum.now(), index, index, "B")._asdict()
            )

        offer_list = [
            Offer("offer_id1", pendulum.now(), 8, 8, "S")._asdict(),
            Offer("offer_id2", pendulum.now(), 4, 4, "S")._asdict(),
            Offer("offer_id3", pendulum.now(), 13, 13, "S")._asdict(),
        ]
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        timeslot = "2021-10-06T12:00"
        current_time = str(pendulum.now())
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offer_list, bid_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        assert len(matches) == 7
        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id1", "bid_id2")
        self.validate_matching(matches[2], 3, "offer_id1", "bid_id3")
        self.validate_matching(matches[3], 2, "offer_id1", "bid_id4")
        self.validate_matching(matches[4], 2, "offer_id2", "bid_id4")
        self.validate_matching(matches[5], 2, "offer_id2", "bid_id5")
        self.validate_matching(matches[6], 3, "offer_id3", "bid_id5")

    def test_create_bid_offer_matches_can_handle_excessive_bid_energy(self):
        bid_list = []
        for index in range(1, 6):
            bid_list.append(
                Bid(f"bid_id{index}", pendulum.now(), index, index, "B")._asdict()
            )

        offer_list = [
            Offer("offer_id1", pendulum.now(), 8, 8, "S")._asdict(),
            Offer("offer_id2", pendulum.now(), 4, 4, "S")._asdict(),
            Offer("offer_id3", pendulum.now(), 5003, 5003, "S")._asdict(),
        ]
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        timeslot = "2021-10-06T12:00"
        current_time = str(pendulum.now())
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offer_list, bid_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        assert len(matches) == 7
        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id1", "bid_id2")
        self.validate_matching(matches[2], 3, "offer_id1", "bid_id3")
        self.validate_matching(matches[3], 2, "offer_id1", "bid_id4")
        self.validate_matching(matches[4], 2, "offer_id2", "bid_id4")
        self.validate_matching(matches[5], 2, "offer_id2", "bid_id5")
        self.validate_matching(matches[6], 3, "offer_id3", "bid_id5")

    def test_create_bid_offer_matches_can_match_with_only_one_offer(self):
        bid_list = []
        for index in range(1, 6):
            bid_list.append(
                Bid(f"bid_id{index}", pendulum.now(), index, index, "B")._asdict()
            )

        offer_list = [
            Offer("offer_id1", pendulum.now(), 8, 800000000, "S")._asdict()
        ]
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        current_time = str(pendulum.now())
        timeslot = "2021-10-06T12:00"
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offer_list, bid_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        assert len(matches) == 5
        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id1", "bid_id2")
        self.validate_matching(matches[2], 3, "offer_id1", "bid_id3")
        self.validate_matching(matches[3], 4, "offer_id1", "bid_id4")
        self.validate_matching(matches[4], 5, "offer_id1", "bid_id5")

    def test_create_bid_offer_matches_can_match_with_only_one_bid(self):
        bids_list = [
            Bid("bid_id1", pendulum.now(), 9, 90123456789, "B")._asdict()
        ]

        offers_list = []
        for index in range(1, 6):
            offers_list.append(
                Offer(f"offer_id{index}", pendulum.now(), index, index, "Seller")._asdict()
            )
        pac_algo = PayAsClearMatchingAlgorithm()
        market_id = str(uuid4())
        current_time = str(pendulum.now())
        timeslot = "2021-10-06T12:00"
        pac_algo.state.clearing[market_id] = {current_time: Clearing(1, 15)}
        matches = pac_algo._create_bid_offer_matches(
            offers_list, bids_list, market_id=market_id, timeslot=timeslot,
            current_time=current_time)

        assert len(matches) == 5
        self.validate_matching(matches[0], 1, "offer_id1", "bid_id1")
        self.validate_matching(matches[1], 2, "offer_id2", "bid_id1")
        self.validate_matching(matches[2], 3, "offer_id3", "bid_id1")
        self.validate_matching(matches[3], 4, "offer_id4", "bid_id1")
        self.validate_matching(matches[4], 5, "offer_id5", "bid_id1")

    def test_get_matches_recommendations(self):
        data = {
            "market1": {
                "2021-10-06T12:00": {
                    "bids": [
                        {"id": 1, "buyer": "A", "energy_rate": 1, "energy": 10},
                        {"id": 2, "buyer": "B", "energy_rate": 2, "energy": 15},
                        {"id": 3, "buyer": "C", "energy_rate": 3, "energy": 20},
                    ],
                    "offers": [
                        {"id": 4, "seller": "A", "energy_rate": 1 + FLOATING_POINT_TOLERANCE,
                         "energy": 25},
                        {"id": 5, "seller": "B", "energy_rate": 5, "energy": 30},
                        {"id": 6, "seller": "C", "energy_rate": 2.4, "energy": 35},
                    ],
                }},
            "market2": {
                "2021-10-06T12:00": {
                    "bids": [
                        {"id": 7, "buyer": "A", "energy_rate": 1.5, "energy": 40},
                        {"id": 8, "buyer": "B", "energy_rate": 2, "energy": 45},
                        {"id": 9, "buyer": "C", "energy_rate": 6, "energy": 50},
                    ],
                    "offers": [
                        {"id": 10, "seller": "A", "energy_rate": 1, "energy": 55},
                        {"id": 11, "seller": "B", "energy_rate": 5, "energy": 60},
                        {"id": 12, "seller": "C", "energy_rate": 1, "energy": 65},
                    ],
                }
            }
        }
        trades = PayAsClearMatchingAlgorithm().get_matches_recommendations(data)
        expected_trades = [{"market_id": "market1",
                            "timeslot": "2021-10-06T12:00",
                            "bids": [{"id": 3, "buyer": "C", "energy_rate": 3, "energy": 20}],
                            "offers": [{"id": 4, "seller": "A", "energy_rate": 1.00001,
                                        "energy": 25}], "selected_energy": 20, "trade_rate": 3},
                           {"market_id": "market2",
                            "timeslot": "2021-10-06T12:00",
                            "bids": [{"id": 9, "buyer": "C", "energy_rate": 6, "energy": 50}],
                            "offers": [{"id": 10, "seller": "A", "energy_rate": 1,
                                        "energy": 55}], "selected_energy": 50, "trade_rate": 2},
                           {"market_id": "market2",
                            "timeslot": "2021-10-06T12:00",
                            "bids": [{"id": 8, "buyer": "B", "energy_rate": 2, "energy": 45}],
                            "offers": [{"id": 10, "seller": "A", "energy_rate": 1, "energy": 55}],
                            "selected_energy": 5, "trade_rate": 2},
                           {"market_id": "market2",
                            "timeslot": "2021-10-06T12:00",
                            "bids": [{"id": 8, "buyer": "B", "energy_rate": 2, "energy": 45}],
                            "offers": [{"id": 12, "seller": "C", "energy_rate": 1,
                                        "energy": 65}], "selected_energy": 40, "trade_rate": 2},
                           ]
        assert trades == expected_trades
