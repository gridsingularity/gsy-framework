from dataclasses import replace
from math import sqrt

import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.data_classes import ReplacementTreatment, SuppressionCause
from gsy_framework.sim_results.roi.indicators import (
    interpolated_crossing,
    internal_rate_of_return,
    sign_changes,
)
from tests.test_sim_results.roi.conftest import (
    IRR_TOLERANCE,
    LCOE_TOLERANCE,
    MONEY_CUMULATIVE_TOLERANCE,
    YEARS_TOLERANCE,
)

DISCRETE_INDICATOR_CELLS = {
    "payback_years": ("B5", YEARS_TOLERANCE),
    "discounted_payback_years": ("B7", YEARS_TOLERANCE),
    "npv": ("B8", MONEY_CUMULATIVE_TOLERANCE),
    "lcoe_per_kwh": ("B11", LCOE_TOLERANCE),
    "lifetime_net_benefit": ("B12", MONEY_CUMULATIVE_TOLERANCE),
}

# The workbook caches only its discrete results. These are its Indicators sheet recalculated
# by the formulas package with Inputs!B42 set to "reserve". The IRR comes from numpy_financial
# on the recalculated CashFlow column I, because formulas evaluates the sign count B9 as 0.
RESERVE_INDICATORS = {
    "payback_years": (10.8025107057, YEARS_TOLERANCE),
    "discounted_payback_years": (14.1115228187, YEARS_TOLERANCE),
    "npv": (3768.5658404018, MONEY_CUMULATIVE_TOLERANCE),
    "irr": (0.0854646921, IRR_TOLERANCE),
    "lcoe_per_kwh": (0.1167922444, LCOE_TOLERANCE),
    "lifetime_net_benefit": (10442.1613576658, MONEY_CUMULATIVE_TOLERANCE),
}


@pytest.fixture(name="indicators_sheet")
def fixture_indicators_sheet(workbook):
    return workbook["Indicators"]


@pytest.fixture(name="result")
def fixture_result(reference_inputs, reference_parameters):
    return calculate_roi(reference_inputs, reference_parameters)


class TestCalculateRoiAgainstWorkbook:

    @pytest.mark.parametrize("indicator_name", list(DISCRETE_INDICATOR_CELLS))
    def test_discrete_matches_workbook(self, result, indicators_sheet, indicator_name):
        # Given
        cell, tolerance = DISCRETE_INDICATOR_CELLS[indicator_name]
        expected = indicators_sheet[cell].value

        # When
        actual = getattr(result, indicator_name).value

        # Then
        assert actual == pytest.approx(expected, abs=tolerance)

    @pytest.mark.parametrize("indicator_name", list(RESERVE_INDICATORS))
    def test_reserve_matches_recalculated_workbook(
        self, reference_inputs, reference_parameters, indicator_name
    ):
        # Given
        inputs = replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)
        expected, tolerance = RESERVE_INDICATORS[indicator_name]

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert getattr(result, indicator_name).value == pytest.approx(expected, abs=tolerance)

    def test_discrete_replacement_suppresses_irr(self, result, indicators_sheet):
        # Given
        expected_sign_changes = indicators_sheet["B9"].value

        # When
        changes = sign_changes(result.series.cash_flow)

        # Then
        assert changes == expected_sign_changes
        assert result.irr.suppressed is SuppressionCause.IRR_NOT_UNIQUE

    def test_annualisation_factor_matches_workbook(self, result, indicators_sheet):
        # Given
        expected = indicators_sheet["B14"].value

        # When
        annualisation = result.annualisation_factor

        # Then
        assert annualisation == pytest.approx(expected)
        assert result.seasonally_unadjusted is False


class TestIndicatorFunctions:

    @pytest.mark.parametrize(
        "balance, cash_flow, expected",
        [
            ([-100, -40, 20, -30, 10], [-100, 60, 60, -50, 40], 1 + 40 / 60),
            ([-100, -40, 0], [-100, 60, 40], 2.0),
        ],
        ids=["first_crossing_wins", "final_balance_of_exactly_zero"],
    )
    def test_payback_interpolates_the_first_crossing(self, balance, cash_flow, expected):
        # Given / When
        crossing = interpolated_crossing(balance, cash_flow)

        # Then
        assert crossing == pytest.approx(expected)

    @pytest.mark.parametrize(
        "cash_flow, expected",
        [([0, -100, 0, 150], sqrt(1.5) - 1), ([-100, 90], -0.1)],
        ids=["leading_zero_flow", "negative_rate"],
    )
    def test_irr_solves_equation_14(self, cash_flow, expected):
        # Given / When
        irr = internal_rate_of_return(cash_flow)

        # Then
        assert irr.value == pytest.approx(expected)


class TestCalculateRoiGuards:

    def test_never_breaking_even_suppresses_both_paybacks(
        self, reference_inputs, reference_parameters
    ):
        # Given
        inputs = replace(reference_inputs, avoided_purchase=1.0, sales_revenue=1.0)

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert result.payback_years.value is None
        assert result.payback_years.suppressed is SuppressionCause.NEVER_BREAKS_EVEN
        assert result.discounted_payback_years.suppressed is SuppressionCause.NEVER_BREAKS_EVEN
        assert result.npv.value < 0

    @pytest.mark.parametrize(
        "changes",
        [
            {"avoided_purchase": 0.0, "sales_revenue": 0.0},
            {"ownership_share": 0.0},
        ],
    )
    def test_non_positive_benefit_keeps_series(
        self, reference_inputs, reference_parameters, changes
    ):
        # Given
        inputs = replace(reference_inputs, **changes)

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert len(result.series.cash_flow) == reference_parameters.horizon_years + 1
        for indicator in (result.payback_years, result.discounted_payback_years, result.irr):
            assert indicator.value is None
            assert indicator.suppressed is SuppressionCause.NON_POSITIVE_BENEFIT
        assert result.npv.value is not None

    @pytest.mark.parametrize(
        "changes, cause",
        [
            ({"capacity_kwp": 0}, SuppressionCause.NO_GENERATION),
            ({"window_generation_kwh": 0}, SuppressionCause.NO_GENERATION),
            ({"window_days": 0.5}, SuppressionCause.WINDOW_TOO_SHORT),
        ],
    )
    def test_unusable_inputs_give_no_result(
        self, reference_inputs, reference_parameters, changes, cause
    ):
        # Given
        inputs = replace(reference_inputs, **changes)

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert result.unavailable is cause
        assert result.series is None
        assert result.payback_years.suppressed is cause

    def test_one_day_window_gives_a_result(self, reference_inputs, reference_parameters):
        # Given
        inputs = replace(reference_inputs, window_days=1)

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert result.unavailable is None
        assert result.series is not None

    @pytest.mark.parametrize("annual_generation_kwh", [None, 0.0, -4900.0])
    def test_seasonally_unadjusted_without_usable_annual_generation(
        self, reference_inputs, reference_parameters, annual_generation_kwh
    ):
        # Given
        inputs = replace(reference_inputs, annual_generation_kwh=annual_generation_kwh)

        # When
        result = calculate_roi(inputs, reference_parameters)

        # Then
        assert result.seasonally_unadjusted is True
        assert result.annualisation_factor == pytest.approx(365 / reference_inputs.window_days)
