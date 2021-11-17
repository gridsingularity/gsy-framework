from typing import Dict, List

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.data_classes import OrdersMatch
from gsy_framework.matching_algorithms import BaseMatchingAlgorithm
from gsy_framework.utils import sort_list_of_dicts_by_attribute


class PayAsBidMatchingAlgorithm(BaseMatchingAlgorithm):
    """Perform pay as bid matching algorithm.

    There are 2 simplistic approaches to the problem
        1. Match the cheapest offer with the most expensive bid. This will favor the sellers
        2. Match the cheapest offer with the cheapest bid. This will favor the buyers,
           since the most affordable offers will be allocated for the most aggressive buyers.
    """

    @classmethod
    def get_matches_recommendations(cls, matching_data: Dict) -> List:
        orders_pairs = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bids = data.get("bids")
                offers = data.get("offers")
                # Sorted bids in descending orders
                sorted_bids = sort_list_of_dicts_by_attribute(bids, "energy_rate", True)
                # Sorted offers in descending order
                sorted_offers = sort_list_of_dicts_by_attribute(offers, "energy_rate", True)
                already_selected_bids = set()
                for offer in sorted_offers:
                    for bid in sorted_bids:
                        if (bid.get("id") in already_selected_bids or
                                offer.get("seller") == bid.get("buyer")):
                            continue
                        if (offer.get("energy_rate") - bid.get(
                                "energy_rate")) <= FLOATING_POINT_TOLERANCE:
                            already_selected_bids.add(bid.get("id"))
                            selected_energy = min(bid.get("energy"), offer.get("energy"))
                            orders_pairs.append(
                                OrdersMatch(
                                    market_id=market_id,
                                    time_slot=time_slot,
                                    bids=[bid], offers=[offer],
                                    selected_energy=selected_energy,
                                    trade_rate=bid.get("energy_rate")).serializable_dict())
                            break
        return orders_pairs
