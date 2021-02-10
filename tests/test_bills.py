import unittest
from uuid import uuid4
from d3a_interface.sim_results.bills import MarketEnergyBills

ACCUMULATED_KEYS_LIST = ["Accumulated Trades", "External Trades", "Totals", "Market Fees"]


class TestBills(unittest.TestCase):

    def setUp(self):
        self.bills = MarketEnergyBills()

    def tearDown(self):
        pass

    @property
    def _empty_bills(self):
        return {
            'bought': 0.0, 'sold': 0.0, 'spent': 0.0, 'earned': 0.0, 'total_energy': 0.0,
            'total_cost': 0.0, 'market_fee': 0.0, 'type': 'Area'
        }

    def create_empty_results_with_children(self, uuid_or_name_list):
        result_dict = {k: self._empty_bills for k in ACCUMULATED_KEYS_LIST}
        result_dict.update({u: self._empty_bills for u in uuid_or_name_list})
        return result_dict

    def test_swap_children_uuids_to_names(self):
        grid_uuid = str(uuid4())
        house1_uuid = str(uuid4())
        house2_uuid = str(uuid4())
        pv_uuid = str(uuid4())
        load_uuid = str(uuid4())
        pv2_uuid = str(uuid4())
        area_dict = {"name": "grid", "uuid": grid_uuid, "parent_uuid": "", "children": [
            {"name": "house1", "uuid": house1_uuid, "parent_uuid": grid_uuid, "children": [
                {"name": "pv", "uuid": pv_uuid, "parent_uuid": house1_uuid, "children": []},
                {"name": "load", "uuid": load_uuid, "parent_uuid": house1_uuid, "children": []}
            ]},
            {"name": "house2", "uuid": house2_uuid, "parent_uuid": grid_uuid, "children": [
                {"name": "pv2", "uuid": pv2_uuid, "parent_uuid": house2_uuid, "children": []},
            ]}
            ]
        }
        uuid_results = {
            grid_uuid: self.create_empty_results_with_children([house1_uuid, house2_uuid]),
            house1_uuid: self.create_empty_results_with_children([pv_uuid, load_uuid]),
            house2_uuid: self.create_empty_results_with_children([pv2_uuid]),
            pv_uuid: self._empty_bills,
            load_uuid: self._empty_bills,
            pv2_uuid: self._empty_bills,
        }
        results = self.bills._swap_children_uuids_to_names(area_dict, uuid_results)
        assert set(results.keys()) == {grid_uuid, house1_uuid, house2_uuid, pv_uuid, load_uuid, pv2_uuid}
        assert set(results[grid_uuid].keys()) == {"house1", "house2", *ACCUMULATED_KEYS_LIST}
        assert set(results[house1_uuid].keys()) == {"pv", "load", *ACCUMULATED_KEYS_LIST}
        assert set(results[house2_uuid].keys()) == {"pv2", *ACCUMULATED_KEYS_LIST}

    def test_bills_local_format(self):
        grid_uuid = str(uuid4())
        house1_uuid = str(uuid4())
        house2_uuid = str(uuid4())
        pv_uuid = str(uuid4())
        load_uuid = str(uuid4())
        pv2_uuid = str(uuid4())
        area_dict = {"name": "grid", "uuid": grid_uuid, "parent_uuid": "", "children": [
            {"name": "house1", "uuid": house1_uuid, "parent_uuid": grid_uuid, "children": [
                {"name": "pv", "uuid": pv_uuid, "parent_uuid": house1_uuid, "children": []},
                {"name": "load", "uuid": load_uuid, "parent_uuid": house1_uuid, "children": []}
            ]},
            {"name": "house2", "uuid": house2_uuid, "parent_uuid": grid_uuid, "children": [
                {"name": "pv2", "uuid": pv2_uuid, "parent_uuid": house2_uuid, "children": []},
            ]}
            ]
        }
        uuid_results = {
            grid_uuid: self.create_empty_results_with_children(["house1", "house2"]),
            house1_uuid: self.create_empty_results_with_children(["pv", "load"]),
            house2_uuid: self.create_empty_results_with_children(["pv2"]),
            pv_uuid: self._empty_bills,
            load_uuid: self._empty_bills,
            pv2_uuid: self._empty_bills,
        }

        uuid_results[grid_uuid]["house1"]["bought"] = 0.987654321

        results = self.bills._bills_local_format(area_dict, uuid_results)
        assert set(results.keys()) == {"grid", "house1", "house2", "load", "pv", "pv2"}
        # Validate that no rounding takes place for the local results
        assert results["grid"]["house1"]["bought"] == 0.987654321

    def test_round_results_for_ui(self):
        uuid_results = {
            "1234": self.create_empty_results_with_children(["house1", "house2"]),
            "2345": self.create_empty_results_with_children(["pv", "load"]),
            "3456": self.create_empty_results_with_children(["pv2"]),
            "4567": self._empty_bills,
            "5678": self._empty_bills,
            "6789": self._empty_bills,
        }

        uuid_results["1234"]["house1"]["bought"] = 0.1234567
        uuid_results["1234"]["house2"]["sold"] = 0.9876541
        uuid_results["2345"]["pv"]["sold"] = 0.987
        uuid_results["6789"]["earned"] = 12
        results = self.bills._round_results_for_ui(uuid_results)
        assert results["1234"]["house1"]["bought"] == 0.123
        assert results["1234"]["house2"]["sold"] == 0.988
        assert results["2345"]["pv"]["sold"] == 0.987
        assert results["6789"]["earned"] == 12
