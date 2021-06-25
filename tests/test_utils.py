import unittest

from d3a_interface.constants_limits import FLOATING_POINT_TOLERANCE
from d3a_interface.utils import (
    HomeRepresentationUtils, perform_pay_as_bid_match, scenario_representation_traversal,
    sort_list_of_dicts_by_attribute)


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.scenario_repr = {
            "name": "grid",
            "children": [
                {"name": "S1 House", "children": [
                    {"name": "Load", "type": "Load"},
                    {"name": "Home Battery", "type": "Storage"}
                ]},
                {"name": "S2 House", "children": [
                    {"name": "Load", "type": "Load"},
                    {"name": "Home Battery", "type": "Storage"},
                    {"name": "Home PV", "type": "PV"}
                ]}
            ]
        }

    def test_scenario_representation_traversal(self):
        areas = list(scenario_representation_traversal(self.scenario_repr))
        assert len(areas) == 8
        assert all(type(obj) == tuple for obj in areas)

    def test_calculate_home_area_stats_from_repr_dict(self):
        home_count, avg_devices_per_home = \
            HomeRepresentationUtils.calculate_home_area_stats_from_repr_dict(self.scenario_repr)
        assert home_count == 2
        assert avg_devices_per_home == 2.5

    def test_sort_list_of_dicts_by_attribute(self):
        input_list = [
            {"id": 1, "energy": 15, "energy_rate": 1, "price": 30},
            {"id": 2, "energy": 20, "energy_rate": 4, "price": 25},
            {"id": 3, "energy": 12, "energy_rate": 3, "price": 77},
            {"id": 4, "energy": 13, "energy_rate": 2, "price": 12},
        ]
        output_list = sort_list_of_dicts_by_attribute(input_list, "price")
        assert [4, 2, 1, 3] == [data["id"] for data in output_list]
        output_list = sort_list_of_dicts_by_attribute(input_list, "price", reverse_order=True)
        assert [3, 1, 2, 4] == [data["id"] for data in output_list]

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
        trades = perform_pay_as_bid_match(data)
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
