from dataclasses import replace

import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.cashflow import annualisation_factor, build_cash_flow_series
from gsy_framework.sim_results.roi.data_classes import ReplacementTreatment
from tests.test_sim_results.roi.conftest import (
    MONEY_CUMULATIVE_TOLERANCE,
    MONEY_PER_YEAR_TOLERANCE,
    cash_flow_column,
)


@pytest.fixture(name="series")
def fixture_series(reference_inputs, reference_parameters):
    return calculate_roi(reference_inputs, reference_parameters).series


class TestAnnualisationFactor:

    @pytest.mark.parametrize("window_days", [365, 366])
    def test_full_year_record_gives_unity(self, window_days):
        # Given / When
        factor = annualisation_factor(4800.0, window_days, 4900.0)

        # Then
        assert factor == (1.0, False)

    def test_multi_year_record_scales_down_to_one_year(self):
        # Given / When
        factor = annualisation_factor(9600.0, 730, 4900.0)

        # Then
        assert factor == (pytest.approx(0.5), False)


class TestCashFlowSeries:

    @pytest.mark.parametrize(
        "attribute, column, tolerance",
        [
            ("cash_flow", "I", MONEY_PER_YEAR_TOLERANCE),
            ("discounted_cash_flow", "L", MONEY_PER_YEAR_TOLERANCE),
            ("asset_operating_cost", "G", MONEY_PER_YEAR_TOLERANCE),
            ("asset_replacement_cost", "H", MONEY_PER_YEAR_TOLERANCE),
            ("balance", "J", MONEY_CUMULATIVE_TOLERANCE),
            ("discounted_balance", "M", MONEY_CUMULATIVE_TOLERANCE),
        ],
    )
    def test_money_series_match_workbook(self, workbook, series, attribute, column, tolerance):
        # Given
        expected = cash_flow_column(workbook, column)

        # When
        actual = getattr(series, attribute)

        # Then
        assert actual == pytest.approx(expected, abs=tolerance)

    def test_generation_matches_workbook(self, workbook, series):
        # Given
        expected = cash_flow_column(workbook, "N")

        # When
        actual = series.generation_kwh

        # Then
        assert actual == pytest.approx(expected)

    def test_reserve_spreads_replacement_up_to_replacement_year(
        self, reference_inputs, reference_parameters
    ):
        # Given
        inputs = replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)
        total = reference_parameters.replacement_cost_per_kwp * inputs.capacity_kwp
        last_reserve_year = reference_parameters.replacement_year
        after_reserve = last_reserve_year + 1

        # When
        series = build_cash_flow_series(inputs, reference_parameters, 1.0)

        # Then
        assert series.asset_replacement_cost[0] == 0
        assert series.asset_replacement_cost[1:after_reserve] == pytest.approx(
            [total / last_reserve_year] * last_reserve_year
        )
        assert not any(series.asset_replacement_cost[after_reserve:])

    def test_ownership_share_apportions_cash_flow_but_not_asset_costs(
        self, reference_inputs, reference_parameters
    ):
        # Given
        half_inputs = replace(reference_inputs, ownership_share=0.5)

        # When
        whole = calculate_roi(reference_inputs, reference_parameters)
        half = calculate_roi(half_inputs, reference_parameters)

        # Then
        assert half.series.cash_flow == pytest.approx(
            [flow / 2 for flow in whole.series.cash_flow]
        )
        assert half.series.asset_operating_cost == whole.series.asset_operating_cost
        assert half.series.asset_replacement_cost == whole.series.asset_replacement_cost
        assert half.lcoe_per_kwh.value == pytest.approx(whole.lcoe_per_kwh.value)
