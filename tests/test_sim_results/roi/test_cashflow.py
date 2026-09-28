from dataclasses import replace

import pytest

from gsy_framework.sim_results.roi.cashflow import annualisation_factor, build_cash_flow_series
from gsy_framework.sim_results.roi.data_classes import ReplacementTreatment
from tests.test_sim_results.roi.conftest import (
    MONEY_CUMULATIVE_TOLERANCE,
    MONEY_PER_YEAR_TOLERANCE,
    cash_flow_column,
)


@pytest.fixture(name="series")
def fixture_series(reference_inputs, reference_parameters):
    annualisation, _ = annualisation_factor(
        reference_inputs.window_generation_kwh,
        reference_inputs.window_days,
        reference_inputs.annual_generation_kwh,
    )
    return build_cash_flow_series(reference_inputs, reference_parameters, annualisation)


def test_annualisation_factor_matches_workbook(workbook, reference_inputs):
    annualisation, seasonally_unadjusted = annualisation_factor(
        reference_inputs.window_generation_kwh,
        reference_inputs.window_days,
        reference_inputs.annual_generation_kwh,
    )
    assert annualisation == pytest.approx(workbook["Inputs"]["B38"].value)
    assert seasonally_unadjusted is False


def test_annualisation_falls_back_to_ratio_of_days():
    assert annualisation_factor(177.0, 7, None) == (pytest.approx(365 / 7), True)


def test_full_year_record_gives_unity():
    assert annualisation_factor(4800.0, 365, 4900.0) == (1.0, False)


@pytest.mark.parametrize(
    "attribute, column",
    [
        ("cash_flow", "I"),
        ("discounted_cash_flow", "L"),
        ("asset_operating_cost", "G"),
        ("asset_replacement_cost", "H"),
    ],
)
def test_yearly_series_match_workbook(workbook, series, attribute, column):
    expected = cash_flow_column(workbook, column)
    assert getattr(series, attribute) == pytest.approx(expected, abs=MONEY_PER_YEAR_TOLERANCE)


@pytest.mark.parametrize("attribute, column", [("balance", "J"), ("discounted_balance", "M")])
def test_balances_match_workbook(workbook, series, attribute, column):
    expected = cash_flow_column(workbook, column)
    assert getattr(series, attribute) == pytest.approx(expected, abs=MONEY_CUMULATIVE_TOLERANCE)


def test_generation_matches_workbook(workbook, series):
    assert series.generation_kwh == pytest.approx(cash_flow_column(workbook, "N"))


def test_reserve_spreads_replacement_up_to_replacement_year(
    reference_inputs, reference_parameters
):
    inputs = replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)
    series = build_cash_flow_series(inputs, reference_parameters, 1.0)
    total = reference_parameters.replacement_cost_per_kwp * inputs.capacity_kwp
    last_reserve_year = reference_parameters.replacement_year
    after_reserve = last_reserve_year + 1

    assert series.asset_replacement_cost[0] == 0
    assert series.asset_replacement_cost[1:after_reserve] == pytest.approx(
        [total / last_reserve_year] * last_reserve_year
    )
    assert not any(series.asset_replacement_cost[after_reserve:])


def test_reserve_keeps_undiscounted_lifetime_net_benefit(reference_inputs, reference_parameters):
    reserve_inputs = replace(reference_inputs, replacement_treatment=ReplacementTreatment.RESERVE)
    discrete = build_cash_flow_series(reference_inputs, reference_parameters, 27.0)
    reserve = build_cash_flow_series(reserve_inputs, reference_parameters, 27.0)
    assert reserve.balance[-1] == pytest.approx(discrete.balance[-1])


def test_ownership_share_apportions_cash_flow_but_not_asset_costs(
    reference_inputs, reference_parameters
):
    whole = build_cash_flow_series(reference_inputs, reference_parameters, 27.0)
    half = build_cash_flow_series(
        replace(reference_inputs, ownership_share=0.5), reference_parameters, 27.0
    )
    assert half.cash_flow == pytest.approx([flow / 2 for flow in whole.cash_flow])
    assert half.asset_operating_cost == whole.asset_operating_cost
    assert half.asset_replacement_cost == whole.asset_replacement_cost
