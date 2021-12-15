from typing import Dict, List

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE
from gsy_framework.data_classes import BidOfferMatch
from gsy_framework.matching_algorithms import BaseMatchingAlgorithm
from gsy_framework.utils import sort_list_of_dicts_by_attribute


class PayAsBidMatchingAlgorithm(BaseMatchingAlgorithm):
    """Perform pay as bid matching algorithm.

    There are 2 simplistic approaches to the problem
        1. Match the cheapest offer with the most expensive bid. This will favor the sellers
        2. Match the cheapest offer with the cheapest bid. This will favor the buyers,
           since the most affordable offers will be allocated for the most aggressive buyers.
    """

    @staticmethod
    def _match_one_bid_one_offer(offer, bid, already_selected_order_energy,
                                 market_id, time_slot):
        if (offer.get("energy_rate") - bid.get(
                "energy_rate")) > FLOATING_POINT_TOLERANCE:
            return None

        if bid["id"] not in already_selected_order_energy:
            already_selected_order_energy[bid["id"]] = bid["energy"]
        if offer["id"] not in already_selected_order_energy:
            already_selected_order_energy[offer["id"]] = offer["energy"]
        offer_energy = already_selected_order_energy[offer["id"]]
        bid_energy = already_selected_order_energy[bid["id"]]

        selected_energy = min(offer_energy, bid_energy)
        if selected_energy <= FLOATING_POINT_TOLERANCE:
            return None

        already_selected_order_energy[bid["id"]] -= selected_energy
        already_selected_order_energy[offer["id"]] -= selected_energy
        assert all(v >= -FLOATING_POINT_TOLERANCE
                   for v in already_selected_order_energy.values()), f"{already_selected_order_energy}"

        return BidOfferMatch(
            market_id=market_id,
            time_slot=time_slot,
            bids=[bid], offers=[offer],
            selected_energy=selected_energy,
            trade_rate=bid.get("energy_rate"))

    @classmethod
    def get_matches_recommendations(cls, matching_data: Dict) -> List:
        bid_offer_pairs = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bids = data.get("bids")
                offers = data.get("offers")
                # Sorted bids in descending orders
                sorted_bids = sort_list_of_dicts_by_attribute(bids, "energy_rate", True)
                # Sorted offers in descending order
                sorted_offers = sort_list_of_dicts_by_attribute(offers, "energy_rate", True)
                already_selected_order_energy = {}
                for offer in sorted_offers:
                    for bid in sorted_bids:
                        if offer.get("seller") == bid.get("buyer"):
                            continue

                        possible_pair = cls._match_one_bid_one_offer(
                            offer, bid, already_selected_order_energy, market_id, time_slot
                        )
                        if possible_pair:
                            bid_offer_pairs.append(possible_pair)

                        if offer["id"] in already_selected_order_energy and \
                                already_selected_order_energy[offer["id"]] <= FLOATING_POINT_TOLERANCE:
                            break
        return [
            pair.serializable_dict() for pair in bid_offer_pairs
        ]
