import unittest

from d3a_interface.utils import count_assets_in_representation


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
                        {"name": "Home Battery", "type": "Storage"}
                    ]}
                ]
            }

    def test_scenario_representation_traversal(self):

        from d3a_interface.utils import scenario_representation_traversal
        areas = list(scenario_representation_traversal(self.scenario_repr))
        assert len(areas) == 7
        assert all(type(obj) == tuple for obj in areas)

    def test_count_assets_in_representation(self):
        assert count_assets_in_representation(self.scenario_repr, "Load") == 2
        assert count_assets_in_representation(self.scenario_repr, "Storage") == 2
