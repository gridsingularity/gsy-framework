from d3a_interface.constants_limits import FLOATING_POINT_TOLERANCE
from d3a_interface.matching_algorithms.pay_as_bid_matching_algorithm import PayAsBidMatchingAlgorithm


class TestPayAsBidMatchingAlgorithm:
    def test_perform_pay_as_bid_match(self):
        data = {
            "market1": {
                "bids": [
                    {"id": 1, "buyer": "A", "energy_rate": 1, "energy": 10},
                    {"id": 2, "buyer": "B", "energy_rate": 2, "energy": 15},
                    {"id": 3, "buyer": "C", "energy_rate": 3, "energy": 20},
                ],
                "offers": [
                    {"id": 4, "seller": "A", "energy_rate": 1 + FLOATING_POINT_TOLERANCE,
                     "energy": 25},
                    {"id": 5, "seller": "B", "energy_rate": 5, "energy": 30},
                    {"id": 6, "seller": "C", "energy_rate": 2.4, "energy": 35},
                ],
            },
            "market2": {
                "bids": [
                    {"id": 7, "buyer": "A", "energy_rate": 1.5, "energy": 40},
                    {"id": 8, "buyer": "B", "energy_rate": 2, "energy": 45},
                    {"id": 9, "buyer": "C", "energy_rate": 6, "energy": 50},
                ],
                "offers": [
                    {"id": 10, "seller": "A", "energy_rate": 1, "energy": 55},
                    {"id": 11, "seller": "B", "energy_rate": 1, "energy": 60},
                    {"id": 12, "seller": "C", "energy_rate": 1, "energy": 65},
                ],
            }
        }
        trades = PayAsBidMatchingAlgorithm.get_matches_recommendations(data)
        expected_trades = [{"market_id": "market1",
                            "bid": {"id": 3, "buyer": "C", "energy_rate": 3, "energy": 20},
                            "offer": {"id": 4, "seller": "A", "energy_rate": 1.00001,
                                      "energy": 25}, "selected_energy": 20, "trade_rate": 3},

                           {"market_id": "market2",
                            "bid": {"id": 9, "buyer": "C", "energy_rate": 6, "energy": 50},
                            "offer": {"id": 10, "seller": "A", "energy_rate": 1, "energy": 55},
                            "selected_energy": 50, "trade_rate": 6},

                           {"market_id": "market2",
                            "bid": {"id": 7, "buyer": "A", "energy_rate": 1.5, "energy": 40},
                            "offer": {"id": 11, "seller": "B", "energy_rate": 1, "energy": 60},
                            "selected_energy": 40, "trade_rate": 1.5},

                           {"market_id": "market2",
                            "bid": {"id": 8, "buyer": "B", "energy_rate": 2, "energy": 45},
                            "offer": {"id": 12, "seller": "C", "energy_rate": 1, "energy": 65},
                            "selected_energy": 45, "trade_rate": 2}]
        assert trades == expected_trades
