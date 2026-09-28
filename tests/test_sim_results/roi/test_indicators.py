from dataclasses import replace

import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.data_classes import ReplacementTreatment, SuppressionCause
from gsy_framework.sim_results.roi.indicators import (
    interpolated_crossing,
    internal_rate_of_return,
    sign_changes,
)
from tests.test_sim_results.roi.conftest import (
    LCOE_TOLERANCE,
    MONEY_CUMULATIVE_TOLERANCE,
    YEARS_TOLERANCE,
)


@pytest.fixture(name="indicators_sheet")
def fixture_indicators_sheet(workbook):
    return workbook["Indicators"]


@pytest.fixture(name="result")
def fixture_result(reference_inputs, reference_parameters):
    return calculate_roi(reference_inputs, reference_parameters)


def test_payback_matches_workbook(result, indicators_sheet):
    assert result.payback_years.value == pytest.approx(
        indicators_sheet["B5"].value, abs=YEARS_TOLERANCE
    )
    assert result.discounted_payback_years.value == pytest.approx(
        indicators_sheet["B7"].value, abs=YEARS_TOLERANCE
    )


def test_money_indicators_match_workbook(result, indicators_sheet):
    assert result.npv.value == pytest.approx(
        indicators_sheet["B8"].value, abs=MONEY_CUMULATIVE_TOLERANCE
    )
    assert result.lifetime_net_benefit.value == pytest.approx(
        indicators_sheet["B12"].value, abs=MONEY_CUMULATIVE_TOLERANCE
    )


def test_lcoe_matches_workbook(result, indicators_sheet):
    assert result.lcoe_per_kwh.value == pytest.approx(
        indicators_sheet["B11"].value, abs=LCOE_TOLERANCE
    )


def test_discrete_replacement_suppresses_irr(result, indicators_sheet):
    assert sign_changes(result.series.cash_flow) == indicators_sheet["B9"].value
    assert indicators_sheet["B10"].value == "n/a"
    assert result.irr.value is None
    assert result.irr.suppressed is SuppressionCause.IRR_NOT_UNIQUE


def test_annualisation_factor_matches_workbook(result, indicators_sheet):
    assert result.annualisation_factor == pytest.approx(indicators_sheet["B14"].value)


def test_reserve_replacement_reports_irr(reference_inputs, reference_parameters):
    inputs = replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)
    result = calculate_roi(inputs, reference_parameters)
    rate = result.irr.value

    assert sign_changes(result.series.cash_flow) == 1
    assert result.irr.suppressed is None
    assert sum(
        flow / (1 + rate) ** year for year, flow in enumerate(result.series.cash_flow)
    ) == pytest.approx(0, abs=1e-6)


def test_payback_uses_first_crossing():
    cash_flow = [-100, 60, 60, -50, 10]
    balance = [-100, -40, 20, -30, -20]
    assert interpolated_crossing(balance, cash_flow) == pytest.approx(1 + 40 / 60)


def test_sign_changes_ignore_zero_flows():
    assert sign_changes([-10, 0, 5, 0, 5]) == 1


def test_irr_of_single_period_project():
    assert internal_rate_of_return([-100, 110]).value == pytest.approx(0.10)


def test_never_breaking_even_suppresses_both_paybacks(reference_inputs, reference_parameters):
    inputs = replace(reference_inputs, avoided_purchase=1.0, sales_revenue=1.0)
    result = calculate_roi(inputs, reference_parameters)

    assert result.payback_years.value is None
    assert result.payback_years.suppressed is SuppressionCause.NEVER_BREAKS_EVEN
    assert result.discounted_payback_years.suppressed is SuppressionCause.NEVER_BREAKS_EVEN
    assert result.npv.value < 0


def test_non_positive_benefit_keeps_series(reference_inputs, reference_parameters):
    inputs = replace(reference_inputs, avoided_purchase=0.0, sales_revenue=0.0)
    result = calculate_roi(inputs, reference_parameters)

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
def test_unusable_inputs_give_no_result(reference_inputs, reference_parameters, changes, cause):
    result = calculate_roi(replace(reference_inputs, **changes), reference_parameters)

    assert result.unavailable is cause
    assert result.series is None
    assert result.payback_years.suppressed is cause


def test_seasonally_unadjusted_without_annual_generation(reference_inputs, reference_parameters):
    result = calculate_roi(
        replace(reference_inputs, annual_generation_kwh=None), reference_parameters
    )
    assert result.seasonally_unadjusted is True
    assert result.annualisation_factor == pytest.approx(365 / reference_inputs.window_days)
