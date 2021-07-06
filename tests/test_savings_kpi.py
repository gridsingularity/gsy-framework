from unittest import TestCase
from uuid import uuid4

from d3a_interface.sim_results.kpi import SavingsKPI


class TestSavingsKPI(TestCase):

    def setUp(self) -> None:
        self.savings_kpi = SavingsKPI()

    def tearDown(self) -> None:
        pass

    def test_populate_consumer_producer_sets_are_correct(self):
        self.pv_uuid = str(uuid4())
        self.load_uuid = str(uuid4())
        self.ess_uuid = str(uuid4())
        test_area = {
             "name": "house",
             "children": [
                 {"name": "pv1", "uuid": self.pv_uuid, "type": "PV", "panel_count": 4},
                 {"name": "load1", "uuid": self.load_uuid, "type": "LoadHoursStrategy",
                  "avg_power_W": 200},
                 {"name": "storage1", "uuid": self.ess_uuid, "type": "StorageExternalStrategy"}
             ]
           }
        self.savings_kpi.populate_consumer_producer_sets(test_area)
        assert self.savings_kpi.producer_ess_set == {self.pv_uuid, self.ess_uuid}
        assert self.savings_kpi.consumer_ess_set == {self.load_uuid, self.ess_uuid}
