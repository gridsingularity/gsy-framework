import pytest
from uuid import uuid4

from d3a_interface.sim_results.kpi import SavingsKPI


@pytest.fixture
def savings_kpi():
    return SavingsKPI()


def test_populate_consumer_producer_sets_are_correct(savings_kpi):
    pv_uuid = str(uuid4())
    load_uuid = str(uuid4())
    ess_uuid = str(uuid4())
    test_area = {
         "name": "house",
         "children": [
             {"name": "pv1", "uuid": pv_uuid, "type": "PV", "panel_count": 4},
             {"name": "load1", "uuid": load_uuid, "type": "LoadHoursStrategy",
              "avg_power_W": 200},
             {"name": "storage1", "uuid": ess_uuid, "type": "StorageExternalStrategy"}
         ]
       }
    savings_kpi.populate_consumer_producer_sets(test_area)
    assert savings_kpi.producer_ess_set == {pv_uuid, ess_uuid}
    assert savings_kpi.consumer_ess_set == {load_uuid, ess_uuid}
