"""
Copyright 2018 Grid Singularity
This file is part of GSy Myco SDK.

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
from copy import deepcopy
from typing import Dict, List, Tuple, Optional

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.data_classes import BidOfferMatch, BaseBidOffer, Bid, Offer
from gsy_framework.matching_algorithms import BaseMatchingAlgorithm
from gsy_framework.matching_algorithms.requirements_validators import (
    RequirementsSatisfiedChecker)
from gsy_framework.utils import sort_list_of_dicts_by_attribute


class PreferredPartnersMatchingAlgorithm(BaseMatchingAlgorithm):
    """Perform PAB matching algorithm on bids trading partners.

    Match the bids with their preferred trading partners offers using the PAB matching algorithm.
    A trading partner is a preferable partner that should be matched with.

    This is a variant of the PAB algorithm, it works as following:
        1. Iterate over markets and time slots' data
        2. For each time slot, iterate over the bids
        3. Against each bid, iterate over the offers
        4. Iterate over requirements of each bid
        5. Make sure there is a `trading_partners` requirement
        6. Iterate over trading partners
        7. Check if there are offers for each partner (from cache {seller_id: [sellers..]})
        8. Iterate over the requirements of the candidate offer
        9. Calculate the match's possible selection of energy and clearing rate
        10. Validate whether the offer/bid can satisfy each other's energy requirements
        11. Create a match recommendation
        12. Check whether the bid can still be matched with more offers
        13. If there is residual energy, repeat the process from step 3
        """

    @classmethod
    def get_matches_recommendations(cls, matching_data: Dict) -> List:
        bid_offer_matches = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bid_offer_matches.extend(cls._calculate_bid_offer_matches_for_one_market_timeslot(
                    market_id, time_slot, data
                ))
        return [
            match.serializable_dict() for match in bid_offer_matches
        ]

    @classmethod
    def _can_order_be_matched(
            cls, bid: Bid.serializable_dict,
            offer: Offer.serializable_dict,
            bid_requirement: Dict, offer_requirement: Dict) -> bool:
        """
        Check if we can match offer & bid taking their selected requirements into consideration.
        """

        offer_required_energy, offer_required_clearing_rate = (
            cls._get_required_energy_and_rate_from_order(offer, offer_requirement))

        bid_required_energy, bid_required_clearing_rate = (
            cls._get_required_energy_and_rate_from_order(bid, bid_requirement))
        if bid_required_clearing_rate < offer_required_clearing_rate:
            return False
        if not (RequirementsSatisfiedChecker.is_bid_requirement_satisfied(
                bid=bid, offer=offer,
                selected_energy=min(offer_required_energy, bid_required_energy),
                clearing_rate=bid_required_clearing_rate,
                bid_requirement=bid_requirement) and
                RequirementsSatisfiedChecker.is_offer_requirement_satisfied(
                    bid=bid, offer=offer,
                    selected_energy=min(
                        offer_required_energy, bid_required_energy),
                    clearing_rate=bid_required_clearing_rate,
                    offer_requirement=offer_requirement)):
            return False
        return True

    @staticmethod
    def _get_actor_to_offers_mapping(
            offers: List[Offer.serializable_dict]
    ) -> Dict[str, List[Offer.serializable_dict]]:
        """Map seller ids/origin ids to their offers list."""
        mapping = {}
        for offer in offers:
            if offer["seller_id"]:
                if offer["seller_id"] not in mapping:
                    mapping[offer["seller_id"]] = []
                mapping[offer["seller_id"]].append(offer)
            if (offer["seller_origin_id"]
                    and offer["seller_origin_id"] != offer["seller_id"]):
                if offer["seller_origin_id"] not in mapping:
                    mapping[offer["seller_origin_id"]] = []
                mapping[offer["seller_origin_id"]].append(offer)
        return mapping

    @classmethod
    def _get_required_energy_and_rate_from_order(
            cls, order: BaseBidOffer.serializable_dict,
            order_requirement: Dict) -> Tuple[float, float]:
        """Determine the energy and clearing rate based on an order + its requirement.

        A bid or offer can have energy and clearing rate attributes on both the instance
        and as a special requirement.
        The values in requirement have higher priority in selecting the energy and rate.

        Args:
            order: a serialized offer or bid structures
            order_requirement: specified requirement dictionary for the order
        """
        order_required_energy = order_requirement.get("energy") or order["energy"]
        if "price" in order_requirement:
            order_required_clearing_rate = (
                order_requirement.get("price") / order_required_energy)
        else:
            order_required_clearing_rate = order["energy_rate"]
        return order_required_energy, order_required_clearing_rate

    @classmethod
    def _calculate_bid_offer_matches_for_one_market_timeslot(
            cls, market_id: str, time_slot: str, data: Dict) -> List[BidOfferMatch]:
        """
        Calculate all possible matches for one market slot.
        """
        bid_offer_matches = []
        bids = data.get("bids")
        offers = data.get("offers")
        # Sorted bids in descending orders
        sorted_bids = sort_list_of_dicts_by_attribute(bids, "energy_rate", True)
        # Sorted offers in descending order
        sorted_offers = sort_list_of_dicts_by_attribute(offers, "energy_rate", True)
        offers_mapping = cls._get_actor_to_offers_mapping(offers)
        available_order_energy = {}
        for bid in sorted_bids:
            for offer in sorted_offers:
                if offer.get("seller") == bid.get("buyer"):
                    continue

                possible_match = cls._match_one_bid_one_offer(
                    offer, bid, available_order_energy, market_id, time_slot, offers_mapping)
                if possible_match:
                    bid_offer_matches.append(possible_match)

                if (bid["id"] in available_order_energy and
                        available_order_energy[bid["id"]] <= FLOATING_POINT_TOLERANCE):
                    break
        return bid_offer_matches

    @classmethod
    def _match_one_bid_one_offer(  # pylint: disable=too-many-arguments, too-many-locals
            cls, offer: Dict, bid: Dict, available_order_energy: Dict,
            market_id: str, time_slot: str, offers_mapping: Dict) -> Optional[BidOfferMatch]:
        """
        Try to match one bid with one offer, and at the same time update the dict with the
        already selected order energy in order to be able to reuse the same order in future
        matches.
        """
        if bid["id"] not in available_order_energy:
            available_order_energy[bid["id"]] = bid["energy"]
        if offer["id"] not in available_order_energy:
            available_order_energy[offer["id"]] = offer["energy"]
        available_offer_energy = available_order_energy[offer["id"]]
        available_bid_energy = available_order_energy[bid["id"]]

        for bid_requirement in bid.get("requirements") or []:
            bid_required_energy, bid_required_clearing_rate = (
                cls._get_required_energy_and_rate_from_order(bid, bid_requirement))
            preferred_offers = []
            for partner in bid_requirement.get("trading_partners") or []:
                preferred_offers.extend(offers_mapping.get(partner) or [])

            for offer_requirement in offer.get("requirements") or [{}]:
                if not cls._can_order_be_matched(
                        bid, offer, bid_requirement, offer_requirement):
                    continue

                offer_required_energy, offer_required_clearing_rate = (
                    cls._get_required_energy_and_rate_from_order(offer, offer_requirement))

                if (
                        offer_required_clearing_rate - bid_required_clearing_rate
                ) > FLOATING_POINT_TOLERANCE:
                    return None

                selected_energy = min(offer_required_energy, bid_required_energy)

                if (selected_energy <= FLOATING_POINT_TOLERANCE or
                        available_offer_energy < selected_energy or
                        available_bid_energy < selected_energy):
                    return None

                recommendation = BidOfferMatch(
                    market_id=market_id,
                    time_slot=time_slot,
                    bid=bid, offer=offer,
                    selected_energy=selected_energy,
                    trade_rate=bid_required_clearing_rate,
                    matching_requirements={
                        "bid_requirement": deepcopy(bid_requirement),
                        "offer_requirement": deepcopy(offer_requirement)
                    })
                available_order_energy[bid["id"]] -= selected_energy
                available_order_energy[offer["id"]] -= selected_energy
                assert all(v >= -FLOATING_POINT_TOLERANCE
                           for v in available_order_energy.values())

                if bid_requirement.get("energy") is not None:
                    bid_requirement["energy"] -= selected_energy
                    assert bid_requirement["energy"] >= -FLOATING_POINT_TOLERANCE

                return recommendation
