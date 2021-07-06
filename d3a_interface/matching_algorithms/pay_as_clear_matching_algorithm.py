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


import math
from logging import getLogger
from collections import OrderedDict
from typing import List, Dict, Tuple

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.dataclasses import MarketClearingState, Clearing, BidOfferMatch
from d3a_interface.matching_algorithms.abstract_matching_algorithm import AbstractMatchingAlgorithm
from d3a_interface.utils import sort_list_of_dicts_by_attribute, add_or_create_key

log = getLogger(__name__)

MATCH_FLOATING_POINT_TOLERANCE = 1e-8


class PayAsClearMatchingAlgorithm(AbstractMatchingAlgorithm):
    """Perform pay as clear matching algorithm.

    bids and offers are aggregated and cleared in a specified clearing interval.
    At the end of each interval, bids are arranged in a descending order, offers in an ascending
    order and the equilibrium quantity of energy and price is calculated.
    The clearing point (the quantity of energy that is accepted trade volume for a specific energy
    rate clearing price) is determined by the point where the arranged bid curve for the buyers
    drops below the offer curve for the sellers.
    """

    STATE = MarketClearingState()
    SORTED_BIDS = []
    SORTED_OFFERS = []

    @classmethod
    def get_matches_recommendations(cls, matching_data):
        for market_id, data in matching_data.items():
            bids = data.get("bids")
            offers = data.get("offers")
            current_time = data.get("current_time")
            clearing = cls.get_clearing_point(bids, offers, current_time)
            if clearing is None:
                return []

            clearing_rate, clearing_energy = clearing
            if clearing_energy > 0:
                log.info(f"Market Clearing Rate: {clearing_rate} "
                         f"||| Clearing Energy: {clearing_energy} ")
            matches = cls._create_bid_offer_matches(
                clearing, cls.SORTED_OFFERS, cls.SORTED_BIDS, market_id
                )
            return matches

    @staticmethod
    def _discrete_point_curve(obj_list, round_functor):
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

    @classmethod
    def _get_clearing_point(cls, max_rate):
        for rate in range(1, max_rate + 1):
            if cls.STATE.cumulative_offers[rate] >= cls.STATE.cumulative_bids[rate]:
                if cls.STATE.cumulative_bids[rate] == 0:
                    return rate-1, cls.STATE.cumulative_offers[rate-1]
                else:
                    return rate, cls.STATE.cumulative_bids[rate]

    @staticmethod
    def _accumulated_energy_per_rate(offer_bids: List[Dict]):
        energy_sum = 0
        accumulated = OrderedDict()
        for offer_bid in offer_bids:
            energy_sum += offer_bid["energy"]
            accumulated[offer_bid["energy_rate"]] = energy_sum
        return accumulated

    @staticmethod
    def _clearing_point_from_supply_demand_curve(bids_rate_energy: Dict, offers_rate_energy: Dict):
        clearing = []
        for b_rate, b_energy in bids_rate_energy.items():
            for o_rate, o_energy in offers_rate_energy.items():
                if o_rate <= (b_rate + MATCH_FLOATING_POINT_TOLERANCE):
                    if o_energy >= b_energy:
                        clearing.append(Clearing(b_rate, b_energy))
        # if cumulative_supply is greater than cumulative_demand
        if len(clearing) > 0:
            return clearing[0].rate, clearing[0].energy
        else:
            for b_rate, b_energy in bids_rate_energy.items():
                for o_rate, o_energy in offers_rate_energy.items():
                    if o_rate <= (b_rate + MATCH_FLOATING_POINT_TOLERANCE) and o_energy < b_energy:
                        clearing.append(Clearing(b_rate, o_energy))
            if len(clearing) > 0:
                return clearing[-1].rate, clearing[-1].energy

    @classmethod
    def get_clearing_point(cls, bids: List[Dict], offers: List[Dict], current_time):
        cls.SORTED_BIDS = sort_list_of_dicts_by_attribute(bids, "energy_rate", True)
        cls.SORTED_OFFERS = sort_list_of_dicts_by_attribute(offers, "energy_rate")
        clearing = None

        if len(cls.SORTED_BIDS) == 0 or len(cls.SORTED_OFFERS) == 0:
            return

        if ConstSettings.IAASettings.PAY_AS_CLEAR_AGGREGATION_ALGORITHM == 1:
            cumulative_bids = cls._accumulated_energy_per_rate(cls.SORTED_BIDS)
            cumulative_offers = cls._accumulated_energy_per_rate(cls.SORTED_OFFERS)
            cls.STATE.cumulative_bids = cumulative_bids
            cls.STATE.cumulative_offers = cumulative_offers
            ascending_rate_bids = OrderedDict(reversed(list(cumulative_bids.items())))
            clearing = cls._clearing_point_from_supply_demand_curve(
                ascending_rate_bids, cumulative_offers)
        elif ConstSettings.IAASettings.PAY_AS_CLEAR_AGGREGATION_ALGORITHM == 2:
            cumulative_bids = cls._discrete_point_curve(cls.SORTED_BIDS, math.floor)
            cumulative_offers = cls._discrete_point_curve(cls.SORTED_OFFERS, math.ceil)
            max_rate = cls._populate_market_cumulative_offer_and_bid(cumulative_bids,
                                                                     cumulative_offers)
            clearing = cls._get_clearing_point(max_rate)
        if clearing is not None:
            cls.STATE.clearing[current_time] = clearing[0]
        return clearing

    @classmethod
    def _populate_market_cumulative_offer_and_bid(cls, cumulative_bids, cumulative_offers):
        max_rate = max(
            math.ceil(cls.SORTED_OFFERS[-1].energy_rate),
            math.floor(cls.SORTED_BIDS[0].energy_rate)
        )
        cls.STATE.cumulative_offers = cls._smooth_discrete_point_curve(
            cumulative_offers, max_rate)
        cls.STATE.cumulative_bids = cls._smooth_discrete_point_curve(
            cumulative_bids, max_rate, False)
        return max_rate

    @classmethod
    def _create_bid_offer_matches(
            cls, clearing: Tuple[float, float],
            offers: List[Dict], bids: List[Dict], market_id: str) -> List[Dict]:
        clearing_rate, clearing_energy = clearing
        # Return value, holds the bid-offer matches
        bid_offer_matches = []
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
                    bid_offer_matches.append(
                        BidOfferMatch(market_id=market_id, bid=bid, selected_energy=bid_energy,
                                      offer=offer, trade_rate=clearing_rate).serializable_dict()
                    )
                    # Update total clearing energy
                    clearing_energy -= bid_energy
                    # Set the bid energy to 0 to move forward to the next bid
                    bid_energy = 0
                else:
                    # Offer is exhausted by the bid. More offers are needed to cover the bid.
                    # Save the matching offer to accept later
                    bid_offer_matches.append(
                        BidOfferMatch(market_id=market_id, bid=bid, selected_energy=offer_energy,
                                      offer=offer, trade_rate=clearing_rate).serializable_dict()
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
                    return bid_offer_matches

        return bid_offer_matches
