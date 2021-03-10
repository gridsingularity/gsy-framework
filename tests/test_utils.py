import unittest


class TestUtils(unittest.TestCase):
    def test_scenario_representation_traversal(self):
        scenario_repr = {
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

        from d3a_interface.utils import scenario_representation_traversal
        areas = list(scenario_representation_traversal(scenario_repr))
        assert len(areas) == 7
        assert all(type(obj) == tuple for obj in areas)
