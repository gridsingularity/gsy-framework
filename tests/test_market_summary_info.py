import unittest
from math import isclose
from gsy_framework.sim_results.market_summary_info import MarketSummaryInfo
from gsy_framework.unit_test_utils import assert_dicts_identical


class TestMarketSummaryInfo(unittest.TestCase):

    def setUp(self):
        self._market_summary_info = MarketSummaryInfo(should_export_plots=False)

    def test_merge_operation_works(self):
        area_result = {
            "average_energy_rate": 0.3,
            "external_traded_volume": 123,
            "traded_volume": 456,
            "timestamp": "2021-01-02T12:43"
        }

        global_results = {"house1_uuid": []}
        market_results = {"house1_uuid": area_result}
        result = self._market_summary_info.merge_results_to_global(market_results, global_results)
        assert_dicts_identical(result, {"house1_uuid": [area_result]})

        global_results = {}
        market_results = {"house1_uuid": area_result}
        result = self._market_summary_info.merge_results_to_global(market_results, global_results)
        assert_dicts_identical(result, {"house1_uuid": [area_result]})

        existing_result = {
            "average_energy_rate": 0.29,
            "external_traded_volume": 321,
            "traded_volume": 654,
            "timestamp": "2021-01-02T12:52"
        }
        global_results = {"house1_uuid": [existing_result]}
        market_results = {"house1_uuid": area_result}
        result = self._market_summary_info.merge_results_to_global(market_results, global_results)
        assert_dicts_identical(result, {"house1_uuid": [existing_result, area_result]})

    def test_update(self):
        area_result_dict = {
            "name": "house1", "uuid": "house1_uuid", "children": [
                {"name": "house2", "uuid": "house2_uuid"},
                {"name": "house3", "uuid": "house3_uuid"}
            ]
        }
        core_stats = {
            "house1_uuid": {"trades": [
                {"seller": "house2", "buyer": "house3", "energy_rate": 0.1, "energy": 0.5},
                {"seller": "house1", "buyer": "house2", "energy_rate": 0.2, "energy": 0.6},
                {"seller": "house3", "buyer": "house1", "energy_rate": 0.3, "energy": 0.7}
            ]}
        }
        self._market_summary_info.update(area_result_dict, core_stats, "2021-02-02T15:32")
        house1_results = self._market_summary_info.raw_results["house1_uuid"]
        assert isclose(house1_results["average_energy_rate"], 0.2)
        assert isclose(house1_results["traded_volume"], 1.8)
        assert isclose(house1_results["external_traded_volume"], 1.3)
        assert house1_results["timestamp"] == "2021-02-02T15:32"

    def test_update_multiple_markets(self):
        area_result_dict = {
            "name": "house1", "uuid": "house1_uuid", "children": [
                {"name": "house2", "uuid": "house2_uuid", "children": [
                    {"name": "house3_1", "uuid": "house3_1_uuid"},
                    {"name": "house3_2", "uuid": "house3_2_uuid"}
                ]},
                {"name": "house4", "uuid": "house4_uuid", "children": [
                    {"name": "house5_1", "uuid": "house5_1_uuid"},
                    {"name": "house5_2", "uuid": "house5_2_uuid"}
                ]},
            ]
        }
        core_stats = {
            "house2_uuid": {"trades": [
                {"seller": "house3_1", "buyer": "house3_2", "energy_rate": 0.1, "energy": 0.5},
                {"seller": "house3_1", "buyer": "house3_2", "energy_rate": 0.1, "energy": 0.5},
                {"seller": "house3_2", "buyer": "house3_1", "energy_rate": 0.1, "energy": 0.5}
            ]},
            "house4_uuid": {"trades": [
                {"seller": "house4", "buyer": "house5_2", "energy_rate": 0.3, "energy": 1},
                {"seller": "house5_1", "buyer": "house4", "energy_rate": 0.2, "energy": 2},
                {"seller": "house5_2", "buyer": "house4", "energy_rate": 0.4, "energy": 3}
            ]}
        }
        self._market_summary_info.update(area_result_dict, core_stats, "2021-03-02T15:59")
        house2_results = self._market_summary_info.raw_results["house2_uuid"]
        assert isclose(house2_results["average_energy_rate"], 0.1)
        assert isclose(house2_results["traded_volume"], 1.5)
        assert isclose(house2_results["external_traded_volume"], 0.0)
        assert house2_results["timestamp"] == "2021-03-02T15:59"

        house4_results = self._market_summary_info.raw_results["house4_uuid"]
        assert isclose(house4_results["average_energy_rate"], 0.3)
        assert isclose(house4_results["traded_volume"], 6)
        assert isclose(house4_results["external_traded_volume"], 6)
        assert house4_results["timestamp"] == "2021-03-02T15:59"
