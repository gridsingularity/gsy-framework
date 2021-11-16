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


from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

from gsy_framework.data_classes import Offer, Bid


class Requirement(ABC):
    """Interface for offer and bid requirements."""

    @classmethod
    @abstractmethod
    def is_satisfied(
            cls, offer: Offer, bid: Bid, requirement: Dict,
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None) -> bool:
        """Check whether a requirement is satisfied."""


class TradingPartnersRequirement(Requirement):
    """Check if trading_partners requirement is satisfied for both bid and offer."""

    @classmethod
    def is_satisfied(cls, offer: Offer, bid: Bid, requirement: Dict,
                     clearing_rate: Optional[float] = None,
                     selected_energy: Optional[float] = None) -> bool:
        trading_partners = requirement.get("trading_partners", [])
        assert isinstance(trading_partners, list),\
            f"Invalid data type for trading partner {requirement}"
        if trading_partners and not (
                bid.buyer_id in trading_partners or
                bid.buyer_origin_id in trading_partners or
                offer.seller_id in trading_partners or
                offer.seller_origin_id in trading_partners):
            return False
        return True


class EnergyTypeRequirement(Requirement):
    """Check if energy_type requirement of bid is satisfied."""

    @classmethod
    def is_satisfied(cls, offer: Offer, bid: Bid, requirement: Dict,
                     clearing_rate: Optional[float] = None,
                     selected_energy: Optional[float] = None) -> bool:
        bid_required_energy_types = requirement.get("energy_type")
        assert isinstance(bid_required_energy_types, list), \
            f"Invalid data type for energy_type {requirement}"
        offer_energy_type = (offer.attributes or {}).get("energy_type", None)
        if not bid_required_energy_types:
            return True
        return offer_energy_type in bid_required_energy_types


class SelectedEnergyRequirement(Requirement):
    """Check if energy (selected energy) requirement of bid is satisfied."""

    @classmethod
    def is_satisfied(cls, offer: Offer, bid: Bid, requirement: Dict,
                     clearing_rate: Optional[float] = None,
                     selected_energy: Optional[float] = None) -> bool:
        bid_required_energy = requirement.get("energy")
        assert isinstance(bid_required_energy, (int, float)), \
            f"Invalid data type for energy {requirement}"
        assert isinstance(selected_energy, (int, float)), \
            f"Invalid data type for selected_energy {selected_energy}"

        return bid_required_energy >= selected_energy


class PriceRequirement(Requirement):
    """Check if price requirement of bid is satisfied."""

    @classmethod
    def is_satisfied(cls, offer: Offer, bid: Bid, requirement: Dict,
                     clearing_rate: Optional[float] = None,
                     selected_energy: Optional[float] = None) -> bool:
        bid_required_price = requirement.get("price")
        assert isinstance(bid_required_price, (int, float)), \
            f"Invalid data type for price {requirement}"
        assert isinstance(selected_energy, (int, float)), \
            f"Invalid data type for selected_energy {selected_energy}"
        assert isinstance(clearing_rate, (int, float)), \
            f"Invalid data type for clearing_rate {clearing_rate}"
        # bid_required_price >= price -> true
        return bid_required_price >= selected_energy * clearing_rate


# Supported offers/bids requirements
# To add a new requirement create a class extending the Requirement abstract class and add it below

SUPPORTED_OFFER_REQUIREMENTS = {
    "trading_partners": TradingPartnersRequirement
}

SUPPORTED_BID_REQUIREMENTS = {
    "trading_partners": TradingPartnersRequirement,
    "energy_type": EnergyTypeRequirement,
    "energy": SelectedEnergyRequirement,
    "price": PriceRequirement
}


class RequirementsSatisfiedChecker:
    """Check if a list of bid/offer requirements are satisfied."""

    @classmethod
    def is_satisfied(
            cls, offer: Union[Offer, Offer.serializable_dict],
            bid: Union[Bid, Bid.serializable_dict],
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None) -> bool:
        """Check whether at least 1 offer and 1 bid requirement are satisfied."""

        offer = Offer.from_dict(offer) if isinstance(offer, dict) else offer
        bid = Bid.from_dict(bid) if isinstance(bid, dict) else bid

        if offer.requirements:
            offer_requirements_satisfied = cls.are_offer_requirements_satisfied(
                offer, bid, clearing_rate, selected_energy)
        else:
            # If the concerned offer has no requirements, consider it as satisfied.
            offer_requirements_satisfied = True

        if bid.requirements:
            bid_requirements_satisfied = cls.are_bid_requirements_satisfied(
                offer, bid, clearing_rate, selected_energy)
        else:
            # If the concerned bid has no requirements, consider it as satisfied.
            bid_requirements_satisfied = True

        return offer_requirements_satisfied and bid_requirements_satisfied

    @staticmethod
    def is_offer_requirement_satisfied(
            offer: Union[Offer, Offer.serializable_dict],
            bid: Union[Bid, Bid.serializable_dict],
            offer_requirement: Dict,
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None):
        """Check whether an offer requirement is satisfied."""
        offer = Offer.from_dict(offer) if isinstance(offer, dict) else offer
        bid = Bid.from_dict(bid) if isinstance(bid, dict) else bid
        return all(key in SUPPORTED_OFFER_REQUIREMENTS
                   and SUPPORTED_OFFER_REQUIREMENTS[key].is_satisfied(
                    offer, bid, offer_requirement, clearing_rate, selected_energy)
                   for key in offer_requirement)

    @staticmethod
    def is_bid_requirement_satisfied(
            offer: Union[Offer, Offer.serializable_dict],
            bid: Union[Bid, Bid.serializable_dict],
            bid_requirement: Dict,
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None):
        """Check whether a bid requirement is satisfied."""
        offer = Offer.from_dict(offer) if isinstance(offer, dict) else offer
        bid = Bid.from_dict(bid) if isinstance(bid, dict) else bid
        return all(key in SUPPORTED_BID_REQUIREMENTS
                   and SUPPORTED_BID_REQUIREMENTS[key].is_satisfied(
                    offer, bid, bid_requirement, clearing_rate, selected_energy)
                   for key in bid_requirement)

    @classmethod
    def are_offer_requirements_satisfied(
            cls, offer: Union[Offer, Offer.serializable_dict],
            bid: Union[Bid, Bid.serializable_dict],
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None):
        """Check whether at least 1 offer requirement is satisfied."""
        offer = Offer.from_dict(offer) if isinstance(offer, dict) else offer
        bid = Bid.from_dict(bid) if isinstance(bid, dict) else bid

        return any(cls.is_offer_requirement_satisfied(
            offer, bid, offer_requirement, clearing_rate, selected_energy
        ) for offer_requirement in offer.requirements)

    @classmethod
    def are_bid_requirements_satisfied(
            cls, offer: Union[Offer, Offer.serializable_dict],
            bid: Union[Bid, Bid.serializable_dict],
            clearing_rate: Optional[float] = None,
            selected_energy: Optional[float] = None):
        """Check whether at least 1 bid requirement is satisfied."""
        offer = Offer.from_dict(offer) if isinstance(offer, dict) else offer
        bid = Bid.from_dict(bid) if isinstance(bid, dict) else bid

        return any(cls.is_bid_requirement_satisfied(
            offer, bid, bid_requirement, clearing_rate, selected_energy
        ) for bid_requirement in bid.requirements)
