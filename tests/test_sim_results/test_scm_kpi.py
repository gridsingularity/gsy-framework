from uuid import uuid4

from pendulum import now

from gsy_framework.sim_results.scm.kpi import SCMKPI, SCMKPIState


class TestSCMKPI:
    # pylint: disable=protected-access

    @staticmethod
    def test_state_method_reports_savings_absolute_correctly():
        state = SCMKPIState()
        state.total_base_energy_cost_excl_revenue = 2.0
        state.total_gsy_e_cost_excl_revenue = 1.0
        assert state.saving_absolute == 1.0

        state.total_base_energy_cost_excl_revenue = 2.0
        state.total_gsy_e_cost_excl_revenue = 2.0
        assert state.saving_absolute == 0.0

        state.total_base_energy_cost_excl_revenue = 1.0
        state.total_gsy_e_cost_excl_revenue = 2.0
        assert state.saving_absolute == -1.0

    @staticmethod
    def test_state_method_reports_savings_precentage_correctly():
        state = SCMKPIState()
        state.total_base_energy_cost_excl_revenue = 2.0
        state.total_gsy_e_cost_excl_revenue = 1.0
        assert state.saving_percentage == 50.0

        state.total_base_energy_cost_excl_revenue = 2.0
        state.total_gsy_e_cost_excl_revenue = 2.0
        assert state.saving_percentage == 0.0

        state.total_base_energy_cost_excl_revenue = 1.0
        state.total_gsy_e_cost_excl_revenue = 2.0
        assert state.saving_percentage == 100.0

    @staticmethod
    def test_self_sufficiency():
        state = SCMKPIState()
        state.total_energy_demanded_wh = 0.
        assert state.self_sufficiency is None

        state.total_self_consumption_wh = 1.0
        state.total_energy_demanded_wh = 1.0
        assert state.self_sufficiency == 1.0

        state.total_self_consumption_wh = 2.0
        state.total_energy_demanded_wh = 1.0
        assert state.self_sufficiency == 1.0

        state.total_self_consumption_wh = 0.5
        state.total_energy_demanded_wh = 1.0
        assert state.self_sufficiency == 0.5

    @staticmethod
    def test_self_consumption():
        state = SCMKPIState()
        state.total_energy_produced_wh = 0.
        assert state.self_consumption is None

        state.total_self_consumption_wh = 1.0
        state.total_energy_produced_wh = 1.0
        assert state.self_consumption == 1.0

        state.total_self_consumption_wh = 2.0
        state.total_energy_produced_wh = 1.0
        assert state.self_consumption == 1.0

        state.total_self_consumption_wh = 0.5
        state.total_energy_produced_wh = 1.0
        assert state.self_consumption == 0.5

    @staticmethod
    def _generate_area_dict(root_uuid):
        return {
            "name": "root",
            "uuid": root_uuid,
            "type": "Area",
            "children": [
                {"name": "PV", "type": "PV", "uuid": str(uuid4()), "parent_uuid": root_uuid},
                {"name": "Load", "type": "Load", "uuid": str(uuid4()), "parent_uuid": root_uuid}
            ]
        }

    @staticmethod
    def _generate_core_stats(root_uuid):
        return {
            root_uuid: {
                "after_meter_data": {
                    "consumption_kWh": 3.0, "production_kWh": 1.0, "self_consumed_energy_kWh": 2.0,
                    "asset_energy_requirements_kWh": {
                        "asset_uuid1": 1.0, "asset_uuid2": -1.1}
                },
                "bills": {
                    "base_energy_bill": 22.0, "base_energy_bill_excl_revenue": 23.0,
                    "gsy_energy_bill": 21.0, "gsy_energy_bill_excl_revenue": 22.0,
                    "sold_to_grid": 19.0, "sold_to_community": 11.0
                }
            }
        }

    def test_scm_kpis_are_updated_correctly(self):
        parent_uuid = str(uuid4())
        area_dict = self._generate_area_dict(parent_uuid)
        core_stats = self._generate_core_stats(parent_uuid)
        kpi = SCMKPI()
        kpi.update(area_dict, core_stats, now())

        state = kpi._state[parent_uuid]
        assert state.total_energy_demanded_wh == 3000.0
        assert state.total_energy_produced_wh == 1000.0
        assert state.total_self_consumption_wh == 2000.0
        assert state.energy_demanded_wh == 3000.0
        assert state.energy_produced_wh == 1000.0
        assert state.self_consumption_wh == 2000.0
        assert state.asset_energy_requirements_kWh == {
            "asset_uuid1": 1.0, "asset_uuid2": -1.1}
        assert state.total_base_energy_cost == 22.0
        assert state.total_base_energy_cost_excl_revenue == 23.0
        assert state.total_gsy_e_cost == 21.0
        assert state.total_gsy_e_cost_excl_revenue == 22.0
        assert state.total_fit_revenue == 30.0
        assert state.base_energy_cost == 22.0
        assert state.base_energy_cost_excl_revenue == 23.0
        assert state.gsy_e_cost == 21.0
        assert state.gsy_e_cost_excl_revenue == 22.0
        assert state.fit_revenue == 30.0

        area_dict = self._generate_area_dict(parent_uuid)
        core_stats = self._generate_core_stats(parent_uuid)
        kpi.update(area_dict, core_stats, now())

        state = kpi._state[parent_uuid]
        assert state.total_energy_demanded_wh == 6000.0
        assert state.total_energy_produced_wh == 2000.0
        assert state.total_self_consumption_wh == 4000.0
        assert state.energy_demanded_wh == 3000.0
        assert state.energy_produced_wh == 1000.0
        assert state.self_consumption_wh == 2000.0
        assert state.asset_energy_requirements_kWh == {
            "asset_uuid1": 2.0, "asset_uuid2": -2.2}
        assert state.total_base_energy_cost == 44.0
        assert state.total_base_energy_cost_excl_revenue == 46.0
        assert state.total_gsy_e_cost == 42.0
        assert state.total_gsy_e_cost_excl_revenue == 44.0
        assert state.total_fit_revenue == 60.0
        assert state.base_energy_cost == 22.0
        assert state.base_energy_cost_excl_revenue == 23.0
        assert state.gsy_e_cost == 21.0
        assert state.gsy_e_cost_excl_revenue == 22.0
        assert state.fit_revenue == 30.0

    @staticmethod
    def test_restore_results_state():
        kpi = SCMKPI()
        area_uuid = str(uuid4())
        kpi.restore_area_results_state(
            {"name": "test area", "type": "Area", "uuid": area_uuid},
            {
                "total_energy_demanded_wh": 10.,
                "total_energy_produced_wh": 11.,
                "total_self_consumption_wh": 12.,
                "total_base_energy_cost": 13.,
                "total_gsy_e_cost": 14.,
                "total_base_energy_cost_excl_revenue": 15.,
                "total_gsy_e_cost_excl_revenue": 16.,
                "total_fit_revenue": 17.,
                "energy_demanded_wh": 18.,
                "energy_produced_wh": 19.,
                "self_consumption_wh": 20.,
                "base_energy_cost": 21.,
                "gsy_e_cost": 22.,
                "base_energy_cost_excl_revenue": 23.,
                "gsy_e_cost_excl_revenue": 24.,
                "fit_revenue": 25.,
            })
        assert area_uuid in kpi._state
        state = kpi._state[area_uuid]
        assert state.total_energy_demanded_wh == 10.
        assert state.total_energy_produced_wh == 11.
        assert state.total_self_consumption_wh == 12.
        assert state.total_base_energy_cost == 13.
        assert state.total_gsy_e_cost == 14.
        assert state.total_base_energy_cost_excl_revenue == 15.
        assert state.total_gsy_e_cost_excl_revenue == 16.
        assert state.total_fit_revenue == 17.
        assert state.energy_demanded_wh == 18.
        assert state.energy_produced_wh == 19.
        assert state.self_consumption_wh == 20.
        assert state.base_energy_cost == 21.
        assert state.gsy_e_cost == 22.
        assert state.base_energy_cost_excl_revenue == 23.
        assert state.gsy_e_cost_excl_revenue == 24.
        assert state.fit_revenue == 25.
