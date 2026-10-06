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


@pytest.fixture(name="reserve_inputs")
def fixture_reserve_inputs(reference_inputs):
    return replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)


class TestCalculateRoiAgainstWorkbook:

    def test_payback_matches_workbook(self, result, indicators_sheet):
        # Given
        expected_payback = indicators_sheet["B5"].value
        expected_discounted_payback = indicators_sheet["B7"].value

        # When
        payback_years = result.payback_years.value
        discounted_payback_years = result.discounted_payback_years.value

        # Then
        assert payback_years == pytest.approx(expected_payback, abs=YEARS_TOLERANCE)
        assert discounted_payback_years == pytest.approx(
            expected_discounted_payback, abs=YEARS_TOLERANCE
        )

    def test_money_indicators_match_workbook(self, result, indicators_sheet):
        # Given
        expected_npv = indicators_sheet["B8"].value
        expected_lifetime_net_benefit = indicators_sheet["B12"].value

        # When
        npv = result.npv.value
        lifetime_net_benefit = result.lifetime_net_benefit.value

        # Then
        assert npv == pytest.approx(expected_npv, abs=MONEY_CUMULATIVE_TOLERANCE)
        assert lifetime_net_benefit == pytest.approx(
            expected_lifetime_net_benefit, abs=MONEY_CUMULATIVE_TOLERANCE
        )

    def test_lcoe_matches_workbook(self, result, indicators_sheet):
        # Given
        expected = indicators_sheet["B11"].value

        # When
        lcoe = result.lcoe_per_kwh.value

        # Then
        assert lcoe == pytest.approx(expected, abs=LCOE_TOLERANCE)

    def test_discrete_replacement_suppresses_irr(self, result, indicators_sheet):
        # Given
        expected_sign_changes = indicators_sheet["B9"].value

        # When
        changes = sign_changes(result.series.cash_flow)

        # Then
        assert changes == expected_sign_changes
        assert indicators_sheet["B10"].value == "n/a"
        assert result.irr.value is None
        assert result.irr.suppressed is SuppressionCause.IRR_NOT_UNIQUE

    def test_annualisation_factor_matches_workbook(self, result, indicators_sheet):
        # Given
        expected = indicators_sheet["B14"].value

        # When
        annualisation = result.annualisation_factor

        # Then
        assert annualisation == pytest.approx(expected)

    def test_reserve_replacement_reports_irr(self, reserve_inputs, reference_parameters):
        # Given / When
        result = calculate_roi(reserve_inputs, reference_parameters)

        # Then
        rate = result.irr.value
        assert sign_changes(result.series.cash_flow) == 1
        assert result.irr.suppressed is None
        assert sum(
            flow / (1 + rate) ** year for year, flow in enumerate(result.series.cash_flow)
        ) == pytest.approx(0, abs=1e-6)

    @pytest.mark.parametrize("indicator_name", list(RESERVE_INDICATORS))
    def test_reserve_matches_recalculated_workbook(
        self, reserve_inputs, reference_parameters, indicator_name
    ):
        # Given
        expected, tolerance = RESERVE_INDICATORS[indicator_name]

        # When
        result = calculate_roi(reserve_inputs, reference_parameters)

        # Then
        assert getattr(result, indicator_name).value == pytest.approx(expected, abs=tolerance)

    def test_lcoe_ignores_ownership_share(self, result, reference_inputs, reference_parameters):
        # Given
        half_inputs = replace(reference_inputs, ownership_share=0.5)

        # When
        half = calculate_roi(half_inputs, reference_parameters)

        # Then
        assert half.lcoe_per_kwh.value == pytest.approx(result.lcoe_per_kwh.value)


class TestIndicatorFunctions:

    def test_payback_uses_first_crossing(self):
        # Given
        cash_flow = [-100, 60, 60, -50, 10]
        balance = [-100, -40, 20, -30, -20]

        # When
        crossing = interpolated_crossing(balance, cash_flow)

        # Then
        assert crossing == pytest.approx(1 + 40 / 60)

    def test_payback_counts_a_final_balance_of_exactly_zero_as_break_even(self):
        # Given
        cash_flow = [-100, 60, 40]
        balance = [-100, -40, 0]

        # When
        crossing = interpolated_crossing(balance, cash_flow)

        # Then
        assert crossing == pytest.approx(2.0)

    def test_sign_changes_ignore_zero_flows(self):
        # Given / When
        changes = sign_changes([-10, 0, 5, 0, 5])

        # Then
        assert changes == 1

    def test_irr_skips_a_leading_zero_flow(self):
        # Given / When
        irr = internal_rate_of_return([0, -100, 0, 150])

        # Then
        assert irr.value == pytest.approx(sqrt(1.5) - 1)

    def test_irr_of_single_period_project(self):
        # Given / When
        irr = internal_rate_of_return([-100, 110])

        # Then
        assert irr.value == pytest.approx(0.10)


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
