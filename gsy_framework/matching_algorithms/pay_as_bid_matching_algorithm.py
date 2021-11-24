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

                        if (offer.get("energy_rate") - bid.get(
                                "energy_rate")) <= FLOATING_POINT_TOLERANCE:
                            already_selected = False
                            if bid["id"] not in already_selected_order_energy:
                                already_selected_order_energy[bid["id"]] = bid["energy"]
                            else:
                                already_selected = True
                            if offer["id"] not in already_selected_order_energy:
                                already_selected_order_energy[offer["id"]] = offer["energy"]
                            else:
                                already_selected = True
                            offer_energy = already_selected_order_energy[offer["id"]]
                            bid_energy = already_selected_order_energy[bid["id"]]

                            selected_energy = min(offer_energy, bid_energy)
                            if selected_energy <= FLOATING_POINT_TOLERANCE:
                                continue

                            already_selected_order_energy[bid["id"]] -= selected_energy
                            already_selected_order_energy[offer["id"]] -= selected_energy
                            assert all(v >= -FLOATING_POINT_TOLERANCE
                                       for v in already_selected_order_energy.values())

                            if not already_selected:
                                bid_offer_pairs.append(
                                    BidOfferMatch(
                                        market_id=market_id,
                                        time_slot=time_slot,
                                        bids=[bid], offers=[offer],
                                        selected_energy=selected_energy,
                                        trade_rate=bid.get("energy_rate")))
                            else:
                                for pair in bid_offer_pairs:
                                    if any(pair_bid["id"] == bid["id"] for pair_bid in pair.bids):
                                        assert not any(pair_offer["id"] == offer["id"]
                                                       for pair_offer in pair.offers)
                                        pair.offers.append(offer)
                                        pair.selected_energy += selected_energy

                                    elif any(pair_offer["id"] == offer["id"] for pair_offer in pair.offers):
                                        assert not any(pair_bid["id"] == bid["id"]
                                                       for pair_bid in pair.bids)
                                        pair.bids.append(bid)
                                        pair.selected_energy += selected_energy

                            if already_selected_order_energy[offer["id"]] <= FLOATING_POINT_TOLERANCE:
                                break
        return [
            pair.serializable_dict() for pair in bid_offer_pairs
        ]
