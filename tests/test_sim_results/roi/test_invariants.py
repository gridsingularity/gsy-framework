from dataclasses import fields, replace
from math import floor

import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.data_classes import Indicator, ReplacementTreatment


@pytest.fixture(name="result", params=list(ReplacementTreatment))
def fixture_result(request, reference_inputs, reference_parameters):
    inputs = replace(reference_inputs, replacement_treatment=request.param)
    return calculate_roi(inputs, reference_parameters)


def test_final_balance_equals_sum_of_cash_flows(result):
    assert result.series.balance[-1] == pytest.approx(sum(result.series.cash_flow))


@pytest.mark.parametrize(
    "indicator_name, balance_name, cash_flow_name",
    [
        ("payback_years", "balance", "cash_flow"),
        ("discounted_payback_years", "discounted_balance", "discounted_cash_flow"),
    ],
)
def test_payback_lies_between_bracketing_years(
    result, indicator_name, balance_name, cash_flow_name
):
    balance = getattr(result.series, balance_name)
    crossing_year = floor(getattr(result, indicator_name).value) + 1

    assert getattr(result.series, cash_flow_name)[crossing_year] > 0
    assert balance[crossing_year - 1] < 0 <= balance[crossing_year]


def test_every_missing_indicator_has_a_cause(result):
    indicators = [
        getattr(result, field.name)
        for field in fields(result)
        if isinstance(getattr(result, field.name), Indicator)
    ]
    for indicator in indicators:
        assert (indicator.value is None) == (indicator.suppressed is not None)
