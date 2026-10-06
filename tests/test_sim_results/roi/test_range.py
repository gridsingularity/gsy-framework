import pytest

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.parameters import EU_2026_1_RANGE
from gsy_framework.sim_results.roi.range import _case_inputs, calculate_range

OWN_CONSUMPTION_KWH = 34.6855
SOLD_KWH = 142.4439


class TestCalculateRange:

    def test_low_and_high_bracket_the_central_case(self, reference_inputs, reference_parameters):
        # Given
        central = calculate_roi(reference_inputs, reference_parameters)

        # When
        cases = calculate_range(
            reference_inputs, reference_parameters, EU_2026_1_RANGE, OWN_CONSUMPTION_KWH, SOLD_KWH
        )

        # Then
        assert cases["low"].npv.value < central.npv.value < cases["high"].npv.value
        assert (
            cases["high"].payback_years.value
            < central.payback_years.value
            < cases["low"].payback_years.value
        )

    def test_high_case_moves_at_most_the_energy_that_was_sold(
        self, reference_inputs, reference_parameters
    ):
        # Given
        sold_kwh = 1.0

        # When
        high_inputs, _ = _case_inputs(
            reference_inputs,
            reference_parameters,
            EU_2026_1_RANGE,
            OWN_CONSUMPTION_KWH,
            sold_kwh,
            index=1,
        )

        # Then
        avoided_rate = reference_inputs.avoided_purchase / OWN_CONSUMPTION_KWH
        assert high_inputs.avoided_purchase == pytest.approx(
            reference_inputs.avoided_purchase + sold_kwh * avoided_rate
        )
        assert high_inputs.sales_revenue == pytest.approx(0.0, abs=1e-12)
