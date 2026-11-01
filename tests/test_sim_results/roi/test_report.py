import json
from dataclasses import replace

import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.data_classes import (
    AllocationBasis,
    BaselineMethod,
    PriceBasis,
    RoiFlag,
)
from gsy_framework.sim_results.roi.report import FailedPVRoiReport, PVRoiReport, RoiBasis
from gsy_framework.sim_results.roi.serialization import serialize_result


@pytest.fixture(name="basis")
def fixture_basis():
    return RoiBasis(
        baseline_method=BaselineMethod.SIMULATION,
        allocation_basis=AllocationBasis.MARKET_CLEARING,
        price_basis=PriceBasis.PROFILE,
        window_start="2026-06-15T00:00:00+00:00",
        window_days=7.0,
        window_is_metered=False,
        ownership_share=1.0,
        capacity_kWp=5.0,
        capital_cost_per_kWp=1300.0,
        annual_generation_kWh=4900.0,
        asset_name="PV",
        owner_name="Community",
        last_realised_year=None,
        inputs_observed=["generation"],
        inputs_assumed=["discount_rate"],
        flags=[RoiFlag.STORAGE_CAPEX_EXCLUDED, RoiFlag.NOT_SEPARABLE],
    )


class TestPVRoiReport:

    def test_adds_the_basis_to_the_serialized_result(
        self, reference_inputs, reference_parameters, basis
    ):
        # Given
        result = calculate_roi(reference_inputs, reference_parameters)

        # When
        report = PVRoiReport(result, basis, 0.5).serializable_dict()

        # Then
        assert report["npv"] == serialize_result(result)["npv"]
        assert report["basis"]["parameter_set_version"] == result.parameter_set_version
        assert report["basis"]["baseline_method"] == "simulation"
        assert report["basis"]["flags"] == ["not_separable", "storage_capex_excluded"]
        assert "member_name" not in report["basis"]
        assert report["self_consumption_ratio"] == 0.5
        assert "range" not in report and "members" not in report
        json.dumps(report)

    def test_nests_the_range_and_the_members(self, reference_inputs, reference_parameters, basis):
        # Given
        result = calculate_roi(reference_inputs, reference_parameters)
        member_basis = replace(
            basis, ownership_share=0.6, member_name="House 1", member_path="Community/House 1"
        )
        member = PVRoiReport(result, member_basis, 0.5)

        # When
        report = PVRoiReport(
            result, basis, 0.5, range={"low": result}, members={"House 1": member}
        ).serializable_dict()

        # Then
        assert report["range"]["low"] == serialize_result(result)
        assert report["members"]["House 1"]["basis"]["member_path"] == "Community/House 1"
        assert report["members"]["House 1"]["basis"]["ownership_share"] == 0.6


def test_a_failed_report_names_the_error():
    assert FailedPVRoiReport("boom").serializable_dict() == {
        "unavailable": "calculation_failed",
        "error": "boom",
    }
