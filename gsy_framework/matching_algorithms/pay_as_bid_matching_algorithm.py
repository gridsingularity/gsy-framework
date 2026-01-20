from decimal import Decimal
from typing import Dict, List, Optional

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
    def _match_one_bid_one_offer(
        offer: Dict, bid: Dict, available_order_energy: Dict, market_id: str, time_slot: str
    ) -> Optional[BidOfferMatch]:
        """
        Try to match one bid with one offer, and at the same time update the dict with the
        already selected order energy in order to be able to reuse the same order in future
        matches.
        """
        if (offer.get("energy_rate") - bid.get("energy_rate")) > FLOATING_POINT_TOLERANCE:
            return None

        if bid["id"] not in available_order_energy:
            available_order_energy[bid["id"]] = Decimal(bid["energy"])
        if offer["id"] not in available_order_energy:
            available_order_energy[offer["id"]] = Decimal(offer["energy"])
        offer_energy = available_order_energy[offer["id"]]
        bid_energy = available_order_energy[bid["id"]]

        selected_energy = Decimal(min(offer_energy, bid_energy))
        if selected_energy <= FLOATING_POINT_TOLERANCE:
            return None

        available_order_energy[bid["id"]] -= selected_energy
        available_order_energy[offer["id"]] -= selected_energy
        assert all(v >= -FLOATING_POINT_TOLERANCE for v in available_order_energy.values())

        return BidOfferMatch(
            market_id=market_id,
            time_slot=time_slot,
            bid=bid,
            offer=offer,
            selected_energy=selected_energy,
            trade_rate=bid.get("energy_rate"),
        )

    @classmethod
    def _calculate_bid_offer_matches_for_one_market_timeslot(
        cls, market_id: str, time_slot: str, data: Dict
    ) -> List[BidOfferMatch]:
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
        available_order_energy = {}
        for offer in sorted_offers:
            for bid in sorted_bids:
                if offer.get("seller") == bid.get("buyer"):
                    continue

                possible_match = cls._match_one_bid_one_offer(
                    offer, bid, available_order_energy, market_id, time_slot
                )
                if possible_match:
                    bid_offer_matches.append(possible_match)

                if (
                    offer["id"] in available_order_energy
                    and available_order_energy[offer["id"]] <= FLOATING_POINT_TOLERANCE
                ):
                    break
        return bid_offer_matches

    @classmethod
    def get_matches_recommendations(cls, matching_data: Dict) -> List:
        bid_offer_matches = []
        for market_id, time_slot_data in matching_data.items():
            for time_slot, data in time_slot_data.items():
                bid_offer_matches.extend(
                    cls._calculate_bid_offer_matches_for_one_market_timeslot(
                        market_id, time_slot, data
                    )
                )
        return [match.serializable_dict() for match in bid_offer_matches]
