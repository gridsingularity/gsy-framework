from dataclasses import replace
from math import inf, nan

import pytest


class TestRoiParameterSet:

    @pytest.mark.parametrize(
        "changes",
        [
            {"horizon_years": 0},
            {"degradation_rate": -0.01},
            {"degradation_rate": 1.0},
            {"discount_rate": -1.0},
            {"retail_escalation_rate": -1.0},
            {"export_escalation_rate": -1.0},
            {"replacement_year": 0},
            {"replacement_year": 26},
        ],
    )
    def test_rejects_parameters_outside_their_domain(self, reference_parameters, changes):
        # Then
        with pytest.raises(ValueError):
            # Given / When
            replace(reference_parameters, **changes)

    @pytest.mark.parametrize(
        "changes",
        [
            {"replacement_year": 25},
            {"degradation_rate": 0.0},
        ],
    )
    def test_accepts_parameters_on_the_edge_of_their_domain(self, reference_parameters, changes):
        # Given / When
        parameters = replace(reference_parameters, **changes)

        # Then
        for name, value in changes.items():
            assert getattr(parameters, name) == value


class TestRoiInputs:

    @pytest.mark.parametrize(
        "changes",
        [
            {"capital_cost_per_kwp": 0.0},
            {"capital_cost_per_kwp": -1300.0},
            {"ownership_share": -0.5},
            {"ownership_share": 1.5},
            {"window_generation_kwh": nan},
            {"avoided_purchase": inf},
            {"annual_generation_kwh": nan},
        ],
    )
    def test_rejects_inputs_outside_their_domain(self, reference_inputs, changes):
        # Then
        with pytest.raises(ValueError):
            # Given / When
            replace(reference_inputs, **changes)
