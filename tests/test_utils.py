import unittest
from d3a_interface.utils import scenario_representation_traversal, HomeRepresentationUtils


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
