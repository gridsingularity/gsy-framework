from dataclasses import replace

import pytest


class TestRoiParameterSet:

    @pytest.mark.parametrize(
        "changes",
        [
            {"horizon_years": 0},
            {"degradation_rate": -0.01},
            {"degradation_rate": 1.0},
            {"discount_rate": -1.0},
            {"replacement_year": 0},
            {"replacement_year": 26},
        ],
    )
    def test_rejects_parameters_outside_their_domain(self, reference_parameters, changes):
        # Then
        with pytest.raises(ValueError):
            # When
            replace(reference_parameters, **changes)

    def test_accepts_replacement_in_the_final_year(self, reference_parameters):
        # When
        parameters = replace(reference_parameters, replacement_year=25)

        # Then
        assert parameters.replacement_year == parameters.horizon_years
