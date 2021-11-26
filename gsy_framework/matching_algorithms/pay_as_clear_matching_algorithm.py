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


import math
from collections import OrderedDict
from logging import getLogger
from typing import List, Dict, Union

from pendulum import DateTime

from gsy_framework.constants_limits import ConstSettings
from gsy_framework.data_classes import MarketClearingState, Clearing, OrdersMatch
from gsy_framework.matching_algorithms import BaseMatchingAlgorithm
from gsy_framework.utils import sort_list_of_dicts_by_attribute, add_or_create_key

log = getLogger(__name__)

MATCH_FLOATING_POINT_TOLERANCE = 1e-8


class PayAsClearMatchingAlgorithm(BaseMatchingAlgorithm):
    """Perform pay as clear matching algorithm.

    bids and offers are aggregated and cleared in a specified clearing interval.
    At the end of each interval, bids are arranged in a descending order, offers in an ascending
    order and the equilibrium quantity of energy and price is calculated.
    The clearing point (the quantity of energy that is accepted trade volume for a specific energy
    rate clearing price) is determined by the point where the arranged bid curve for the buyers
    drops below the offer curve for the sellers.
    """
    def __init__(self):
        self.state = MarketClearingState()
        self.sorted_bids = []
        self.sorted_offers = []

    def get_matches_recommendations(self, matching_data: Dict) -> List:
        """Returns the recommended bid offer matches"""
        matches = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bids = data.get("bids")
                offers = data.get("offers")
                current_time = data.get("current_time")
                clearing = self.get_clearing_point(bids, offers, current_time, market_id)
                if clearing is None:
                    return []

                if clearing.energy > 0:
                    log.info(f"Market Clearing Rate: {clearing.rate} "
                             f"||| Clearing Energy: {clearing.energy} ")
                matches.extend(self._create_orders_matches(
                    self.sorted_offers, self.sorted_bids, market_id, time_slot, current_time))
        return matches

    @staticmethod
    def _discrete_point_curve(obj_list, round_functor):
        """Create a dict with rounded energy rate as key and value as
        cumulative energy of bids/offers"""
        cumulative = {}
        for obj in obj_list:
            rate = round_functor(obj["energy_rate"])
            cumulative = add_or_create_key(cumulative, rate, obj["energy"])
        return cumulative

    @staticmethod
    def _smooth_discrete_point_curve(obj, limit, asc_order=True):
        if asc_order:
            for i in range(limit + 1):
                obj[i] = obj.get(i, 0) + obj.get(i - 1, 0)
        else:
            for i in range(limit, 0, -1):
                obj[i] = obj.get(i, 0) + obj.get(i + 1, 0)
        return obj

    @staticmethod
    def _get_clearing_point(max_rate: int, cumulative_bids: OrderedDict,
                            cumulative_offers: OrderedDict) -> (int, float):
        """Get the energy rate and cumulative energy at the point of equilibrium."""
        for rate in range(1, max_rate + 1):
            if cumulative_offers[rate] >= cumulative_bids[rate]:
                if cumulative_bids[rate] == 0:
                    return rate-1, cumulative_offers[rate-1]
                return Clearing(rate, cumulative_bids[rate])

    @staticmethod
    def _accumulated_energy_per_rate(orders: List[Dict]) -> OrderedDict:
        """Return an ordered dict with with key as energy rate and value as accumulated
        energy at that point"""
        energy_sum = 0
        accumulated = OrderedDict()
        for orders in orders:
            energy_sum += orders["energy"]
            accumulated[orders["energy_rate"]] = energy_sum
        return accumulated

    @staticmethod
    def _clearing_point_from_supply_demand_curve(
            bids_rate_energy: Dict, offers_rate_energy: Dict) -> Clearing:
        """Sweeps over ordered dict having cumulative bids and offers incrementally at energy rate
        to find clearing point"""
        clearing = []
        for b_rate, b_energy in bids_rate_energy.items():
            for o_rate, o_energy in offers_rate_energy.items():
                if o_rate <= (b_rate + MATCH_FLOATING_POINT_TOLERANCE):
                    if o_energy >= b_energy:
                        clearing.append(Clearing(b_rate, b_energy))
        # if cumulative_supply is greater than cumulative_demand
        if len(clearing) > 0:
            return clearing[0]
        else:
            for b_rate, b_energy in bids_rate_energy.items():
                for o_rate, o_energy in offers_rate_energy.items():
                    if o_rate <= (b_rate + MATCH_FLOATING_POINT_TOLERANCE) and o_energy < b_energy:
                        clearing.append(Clearing(b_rate, o_energy))
            if len(clearing) > 0:
                return clearing[-1]

    def get_clearing_point(self, bids: List[Dict], offers: List[Dict], current_time: DateTime,
                           market_id: str) -> Union[Clearing, None]:
        """Sorts Bids and Offers and find the equilibrium point"""
        self.sorted_bids = sort_list_of_dicts_by_attribute(bids, "energy_rate", True)
        self.sorted_offers = sort_list_of_dicts_by_attribute(offers, "energy_rate")
        clearing, cumulative_bids, cumulative_offers = None, None, None

        if len(self.sorted_bids) == 0 or len(self.sorted_offers) == 0:
            return

        if ConstSettings.MASettings.PAY_AS_CLEAR_AGGREGATION_ALGORITHM == 1:
            cumulative_bids = self._accumulated_energy_per_rate(self.sorted_bids)
            cumulative_offers = self._accumulated_energy_per_rate(self.sorted_offers)
            ascending_rate_bids = OrderedDict(reversed(list(cumulative_bids.items())))
            clearing = self._clearing_point_from_supply_demand_curve(
                ascending_rate_bids, cumulative_offers)
        elif ConstSettings.MASettings.PAY_AS_CLEAR_AGGREGATION_ALGORITHM == 2:
            cumulative_bids = self._discrete_point_curve(self.sorted_bids, math.floor)
            cumulative_offers = self._discrete_point_curve(self.sorted_offers, math.ceil)
            max_rate, cumulative_bids, cumulative_offers = (
                self._populate_market_cumulative_offer_and_bid(cumulative_bids, cumulative_offers))
            clearing = self._get_clearing_point(max_rate, cumulative_bids, cumulative_offers)
        if clearing is not None:
            self.state.cumulative_bids[market_id] = {current_time: cumulative_bids}
            self.state.cumulative_offers[market_id] = {current_time: cumulative_offers}
            self.state.clearing[market_id] = {current_time: clearing}
        return clearing

    def _populate_market_cumulative_offer_and_bid(self, cumulative_bids, cumulative_offers):
        max_rate = max(
            math.ceil(self.sorted_offers[-1].energy_rate),
            math.floor(self.sorted_bids[0].energy_rate)
        )
        cumulative_offers = self._smooth_discrete_point_curve(
            cumulative_offers, max_rate)
        cumulative_bids = self._smooth_discrete_point_curve(
            cumulative_bids, max_rate, False)
        return max_rate, cumulative_bids, cumulative_offers

    def _create_orders_matches(self, offers: List[Dict], bids: List[Dict], market_id: str,
                               time_slot: str, current_time: str) -> List[Dict]:
        clearing_rate = self.state.clearing[market_id][current_time].rate
        clearing_energy = self.state.clearing[market_id][current_time].energy
        # Return value, holds the bid-offer matches
        orders_matches = []
        # Keeps track of the residual energy from offers that have been matched once,
        # in order for their energy to be correctly tracked on following bids
        residual_offer_energy = {}
        for bid in bids:
            bid_energy = bid["energy"]
            while bid_energy > MATCH_FLOATING_POINT_TOLERANCE:
                # Get the first offer from the list
                offer = offers.pop(0)
                # See if this offer has been matched with another bid beforehand.
                # If it has, fetch the offer energy from the residual dict
                # Otherwise, use offer energy as is.
                offer_energy = residual_offer_energy.get(offer["id"], offer["energy"])
                if offer_energy - bid_energy > MATCH_FLOATING_POINT_TOLERANCE:
                    # Bid energy completely covered by offer energy
                    # Update the residual offer energy to take into account the matched offer
                    residual_offer_energy[offer["id"]] = offer_energy - bid_energy
                    # Place the offer at the front of the offer list to cover following bids
                    # since the offer still has some energy left
                    offers.insert(0, offer)
                    # Save the matching
                    orders_matches.append(
                        OrdersMatch(market_id=market_id, time_slot=time_slot,
                                    bids=[bid], selected_energy=bid_energy,
                                    offers=[offer], trade_rate=clearing_rate).serializable_dict()
                    )
                    # Update total clearing energy
                    clearing_energy -= bid_energy
                    # Set the bid energy to 0 to move forward to the next bid
                    bid_energy = 0
                else:
                    # Offer is exhausted by the bid. More offers are needed to cover the bid.
                    # Save the matching offer to accept later
                    orders_matches.append(
                        OrdersMatch(
                            market_id=market_id, time_slot=time_slot,
                            bids=[bid], selected_energy=offer_energy,
                            offers=[offer], trade_rate=clearing_rate).serializable_dict()
                    )
                    # Subtract the offer energy from the bid, in order to not be taken into account
                    # from following matches
                    bid_energy -= offer_energy
                    # Remove the offer from the residual offer dictionary
                    residual_offer_energy.pop(offer["id"], None)
                    # Update total clearing energy
                    clearing_energy -= offer_energy
                if clearing_energy <= MATCH_FLOATING_POINT_TOLERANCE:
                    # Clearing energy has been satisfied by existing matches. Return the matches
                    return orders_matches

        return orders_matches
