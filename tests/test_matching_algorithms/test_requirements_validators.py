from unittest.mock import MagicMock, patch

import pytest
from pendulum import now

from gsy_framework.data_classes import Offer, Bid, TraderDetails
from gsy_framework.matching_algorithms.requirements_validators import (
    EnergyTypeRequirement,
    TradingPartnersRequirement,
    RequirementsSatisfiedChecker, SelectedEnergyRequirement, PriceRequirement)


@pytest.fixture(name="offer")
def fixture_offer():
    return Offer("id", now(), 2, 2, TraderDetails("other", ""), 2)


@pytest.fixture(name="bid")
def fixture_bid():
    return Bid("bid_id", now(), 9, 10, TraderDetails("B", ""), 9)


@pytest.mark.skip("Order requirements feature disabled.")
class TestRequirementsValidator:
    """Test all bid/offer requirements validators."""

    @staticmethod
    def test_trading_partners_requirement(offer, bid):
        requirement = {"trading_partners": "buyer1"}
        with pytest.raises(AssertionError):
            # trading partners is not of type list
            TradingPartnersRequirement.is_satisfied(offer, bid, requirement)
        # Test offer requirement
        bid.buyer = TraderDetails(bid.buyer.name, "buyer", bid.buyer.origin, bid.buyer.origin_uuid)
        requirement = {"trading_partners": ["buyer1"]}
        offer.requirements = [requirement]
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is False
        requirement = {"trading_partners": ["buyer"]}
        offer.requirements = [requirement]
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is True
        bid.buyer = TraderDetails(bid.buyer.name, "buyer1", bid.buyer.origin, "buyer")
        # still should pass
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is True

        # Test bid requirement
        offer.seller = TraderDetails(
            offer.seller.name, "seller", offer.seller.origin, offer.seller.origin_uuid)
        requirement = {"trading_partners": ["seller1"]}
        bid.requirements = [requirement]
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is False
        requirement = {"trading_partners": ["seller"]}
        bid.requirements = [requirement]
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is True
        offer.seller = TraderDetails(offer.seller.name, "seller1", offer.seller.origin, "seller")
        # still should pass
        assert TradingPartnersRequirement.is_satisfied(offer, bid, requirement) is True

    @staticmethod
    def test_energy_type_requirement(offer, bid):
        requirement = {"energy_type": "Green"}
        with pytest.raises(AssertionError):
            # energy type is not of type list
            EnergyTypeRequirement.is_satisfied(offer, bid, requirement)
        offer.attributes = {"energy_type": "Green"}
        requirement = {"energy_type": ["Grey"]}
        bid.requirements = [requirement]
        assert EnergyTypeRequirement.is_satisfied(offer, bid, requirement) is False
        requirement = {"energy_type": ["Grey", "Green"]}
        assert EnergyTypeRequirement.is_satisfied(offer, bid, requirement) is True

    @staticmethod
    def test_selected_energy_requirement(offer, bid):
        requirement = {"energy": "1"}
        with pytest.raises(AssertionError):
            # energy is not of type float
            SelectedEnergyRequirement.is_satisfied(
                offer, bid, requirement, selected_energy=2)
        requirement = {"energy": 1}
        with pytest.raises(AssertionError):
            # selected energy is not passed
            SelectedEnergyRequirement.is_satisfied(
                offer, bid, requirement)
        requirement = {"energy": 10}
        bid.requirements = [requirement]
        assert SelectedEnergyRequirement.is_satisfied(
            offer, bid, requirement, selected_energy=12) is False
        requirement = {"energy": 10}
        bid.requirements = [requirement]
        assert SelectedEnergyRequirement.is_satisfied(
            offer, bid, requirement, selected_energy=9) is True

    @staticmethod
    def test_price_requirement(offer, bid):
        requirement = {"price": "1"}
        with pytest.raises(AssertionError):
            # price is not of type float
            PriceRequirement.is_satisfied(
                offer, bid, requirement, clearing_rate=2)
        requirement = {"price": 1}
        with pytest.raises(AssertionError):
            # selected clearing_rate and selected energy are not passed
            PriceRequirement.is_satisfied(
                offer, bid, requirement)
        requirement = {"price": 8}
        bid.requirements = [requirement]
        # required price is greater than the clearing_rate * selected_energy
        assert PriceRequirement.is_satisfied(
            offer, bid, requirement, clearing_rate=10, selected_energy=1) is False
        requirement = {"price": 8}
        bid.requirements = [requirement]
        assert PriceRequirement.is_satisfied(
            offer, bid, requirement, clearing_rate=8, selected_energy=1) is True

    @staticmethod
    @patch(
        "gsy_framework.matching_algorithms.requirements_validators."
        "TradingPartnersRequirement.is_satisfied", MagicMock())
    def test_requirements_validator(offer, bid):
        # Empty requirement, should be satisfied
        offer.requirements = [{}]
        assert RequirementsSatisfiedChecker.is_satisfied(offer, bid) is True

        offer.requirements = [{"trading_partners": ["x"]}]
        RequirementsSatisfiedChecker.is_satisfied(offer, bid)
        # pylint: disable=no-member
        TradingPartnersRequirement.is_satisfied.assert_called_once()
