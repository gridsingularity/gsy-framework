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
from d3a_interface.data_classes import BidOfferMatch


class TestBidOfferMatch:
    """Tester class for the BidOfferMatch dataclass."""

    @staticmethod
    def test_serializable_dict():
        """Test the serializable_dict method of BidOfferMatch dataclass."""
        bid_offer_match = BidOfferMatch(
            market_id="market_id",
            bids=[{"type": "bid"}],
            offers=[{"type": "offer"}],
            selected_energy=1,
            trade_rate=1)
        expected_dict = {"market_id": "market_id",
                         "bids": [{"type": "bid"}],
                         "offers": [{"type": "offer"}],
                         "selected_energy": 1,
                         "trade_rate": 1}
        assert bid_offer_match.serializable_dict() == expected_dict

    @staticmethod
    def test_is_valid_dict():
        """Test the is_valid_dict method of BidOfferMatch dataclass."""
        bid_offer_match = {"market_id": "market_id",
                           "bids": [{"type": "bid"}],
                           "offers": [{"type": "offer"}],
                           "selected_energy": 1,
                           "trade_rate": 1}
        assert BidOfferMatch.is_valid_dict(bid_offer_match)

        # Key does not exist
        bid_offer_match = {"market_id": "market_id",
                           "bids": [{"type": "bid"}],
                           "offers": [{"type": "offer"}],
                           "selected_energy": 1,
                           }
        assert not BidOfferMatch.is_valid_dict(bid_offer_match)

        # Wrong type
        bid_offer_match = {"market_id": "market_id",
                           "bids": [{"type": "bid"}],
                           "offers": [{"type": "offer"}],
                           "selected_energy": 1,
                           "trade_rate": ""}
        assert not BidOfferMatch.is_valid_dict(bid_offer_match)

    @staticmethod
    def test_from_dict():
        """Test the from_dict method of BidOfferMatch dataclass."""
        expected_dict = {"market_id": "market_id",
                         "bids": [{"type": "bid"}],
                         "offers": [{"type": "offer"}],
                         "selected_energy": 1,
                         "trade_rate": 1}
        bid_offer_match = BidOfferMatch.from_dict(expected_dict)
        assert bid_offer_match.market_id == expected_dict["market_id"]
        assert bid_offer_match.bids == expected_dict["bids"]
        assert bid_offer_match.offers == expected_dict["offers"]
        assert bid_offer_match.selected_energy == expected_dict["selected_energy"]
        assert bid_offer_match.trade_rate == expected_dict["trade_rate"]
