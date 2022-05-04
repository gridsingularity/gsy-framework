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
from copy import deepcopy
from typing import Dict, Union, List, Tuple, Iterable

from gsy_framework.data_classes import BidOfferMatch
from gsy_framework.matching_algorithms import BaseMatchingAlgorithm, PayAsBidMatchingAlgorithm
from gsy_framework.matching_algorithms.preferred_partners_algorithm import \
    PreferredPartnersMatchingAlgorithm


class AttributedMatchingAlgorithm(BaseMatchingAlgorithm):
    """Perform attributed bid offer matching using pay as bid algorithm.

    The algorithm aggregates related offers/bids based on the following:
        1. Preferred trading partner.
        2. Green tagged energy.
        3. All unmatched yet.

    Aggregated lists will be matched with the pay_as_bid algorithm.
    """

    @classmethod
    def get_matches_recommendations(
            cls, matching_data: Dict[str, Dict]) -> List[BidOfferMatch.serializable_dict]:
        recommendations = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bids_mapping = {bid["id"]: bid for bid in data.get("bids") or []}
                offers_mapping = {offer["id"]: offer for offer in data.get("offers") or []}

                if not (bids_mapping and offers_mapping):
                    continue
                # Trading partners matching
                trading_partners_recommendations = (
                    PreferredPartnersMatchingAlgorithm.get_matches_recommendations(
                        {market_id: {time_slot: data}}))

                bids_mapping, offers_mapping = cls._filter_out_consumed_orders(
                    bids_mapping, offers_mapping, trading_partners_recommendations)

                # Green energy matching
                green_recommendations = cls._perform_green_matching(
                    market_id, time_slot, offers_mapping, bids_mapping)

                bids_mapping, offers_mapping = cls._filter_out_consumed_orders(
                    bids_mapping, offers_mapping, green_recommendations)

                # Residual matching
                residual_recommendations = PayAsBidMatchingAlgorithm.get_matches_recommendations(
                        {market_id: {time_slot: {
                            "bids": bids_mapping.values(),
                            "offers": offers_mapping.values()}}})

                recommendations.extend(
                    trading_partners_recommendations
                    + green_recommendations
                    + residual_recommendations)

        return recommendations

    @classmethod
    def _perform_green_matching(cls, market_id: str,
                                time_slot: str,
                                offers_mapping: Dict,
                                bids_mapping: Dict) -> List[Dict]:
        """Check bids that require green energy and match them with valid offers."""
        green_offers = cls._filter_orders_by_attribute(
            list(offers_mapping.values()), "energy_type", "PV")
        green_bids = cls._filter_orders_by_requirement(
            bids_mapping.values(), "energy_type", "PV")
        return PayAsBidMatchingAlgorithm.get_matches_recommendations(
            {market_id: {time_slot: {"bids": green_bids, "offers": green_offers}}})

    @classmethod
    def _filter_orders_by_requirement(
            cls, orders: Iterable, requirement_key: str,
            requirement_value: Union[str, int, float]) -> List[Dict]:
        """Return a list of offers or bids which have a requirement == specified value."""
        filtered_list = []
        for order in orders:
            for requirement in order.get("requirements") or []:
                if requirement_key not in requirement:
                    continue
                if (isinstance(requirement.get(requirement_key), list)
                        and requirement_value in requirement.get(requirement_key)
                        or requirement_value == requirement.get(requirement_key)):
                    filtered_list.append(order)
                    break
        return filtered_list

    @classmethod
    def _filter_orders_by_attribute(
            cls, orders: list, attribute_key: str,
            attribute_value: Union[str, int, float]) -> List[Dict]:
        """Return a list of offers or bids which have an attribute == specified value."""
        filtered_list = []
        for order in orders:
            if attribute_key not in (order.get("attributes") or {}):
                continue
            if (isinstance(order["attributes"].get(attribute_key), list)
                    and attribute_value in order["attributes"].get(attribute_key)
                    or attribute_value == order["attributes"].get(attribute_key)):
                filtered_list.append(order)
        return filtered_list

    @classmethod
    def _filter_out_consumed_orders(
            cls, bids_mapping: Dict[str, Dict], offers_mapping: Dict[str, Dict],
            recommendations: List[BidOfferMatch.serializable_dict]) -> Tuple[Dict, Dict]:
        """Return bids/offers lists that are not present in the recommendations yet."""
        open_bids_mapping = deepcopy(bids_mapping)
        open_offers_mapping = deepcopy(offers_mapping)
        for recommendation in recommendations:
            open_bids_mapping.pop(recommendation["bid"]["id"], None)
            open_offers_mapping.pop(recommendation["offer"]["id"], None)
        return open_bids_mapping, open_offers_mapping
