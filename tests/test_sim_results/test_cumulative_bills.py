import uuid
from math import isclose

from pendulum import now

from gsy_framework.constants_limits import ConstSettings
from gsy_framework.sim_results.bills import CumulativeBills


class TestCumulativeBills:

    def setup_method(self):
        self._bills = CumulativeBills()

    def teardown_method(self):
        pass

    def test_update_cumulative_bills_works(self):
        seller_name = "test_area"
        seller_uuid = str(uuid.uuid4())
        buyer_name = "buyer_area"
        buyer_uuid = str(uuid.uuid4())
        root_uuid = str(uuid.uuid4())
        area_dict = {
            "name": "root",
            "uuid": root_uuid,
            "type": "Area",
            "children": [
                {"name": seller_name, "type": "PV", "uuid": seller_uuid, "parent_uuid": root_uuid},
                {"name": buyer_name, "type": "Load", "uuid": buyer_uuid, "parent_uuid": root_uuid}
            ]
        }
        core_stats = {
            seller_uuid: {
                "available_energy_kWh": 0.12
            },
            buyer_uuid: {
                "energy_requirement_kWh": 0.05
            },
            root_uuid: {
                "trades": [
                    {
                        "seller": seller_name,
                        "buyer": buyer_name,
                        "energy": 0.5,
                        "price": 0.21,
                        "fee_price": 0.02
                    }],
            }
        }
        ConstSettings.PVSettings.PV_PENALTY_RATE = 50
        ConstSettings.LoadSettings.LOAD_PENALTY_RATE = 50

        self._bills.update(area_dict, core_stats, now())
        assert self._bills.cumulative_bills[seller_uuid]["name"] == seller_name
        # Equal to the available_energy_kWh (production not sold)
        assert self._bills.cumulative_bills[seller_uuid]["penalty_energy"] == 0.12
        # Equals to penalty_energy * PV_PENALTY_RATE / 100.0
        assert self._bills.cumulative_bills[seller_uuid]["penalties"] == 0.12 * 0.5
        # Equals to the trade price since the PV is the seller
        assert self._bills.cumulative_bills[seller_uuid]["earned"] == 0.002
        # Equals to penalties - earned
        assert isclose(self._bills.cumulative_bills[seller_uuid]["total"], 0.06-0.002)

        assert self._bills.cumulative_bills[buyer_uuid]["name"] == buyer_name
        # Equal to the energy_requirement_kWh (consumption not bought)
        assert self._bills.cumulative_bills[buyer_uuid]["penalty_energy"] == 0.05
        # Equals to penalty_energy * LOAD_PENALTY_RATE / 100.0
        assert self._bills.cumulative_bills[buyer_uuid]["penalties"] == 0.05 * 0.5
        # Equals to the trade price since the Load is the buyer
        assert self._bills.cumulative_bills[buyer_uuid]["spent_total"] == 0.002
        # Equals to penalties + spent
        assert isclose(self._bills.cumulative_bills[buyer_uuid]["total"], 0.027)
