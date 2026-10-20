import json
from dataclasses import replace

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.serialization import serialize_result


class TestSerializeResult:

    def test_reference_result_is_json_safe_and_names_each_suppression(
        self, reference_inputs, reference_parameters
    ):
        # Given
        result = calculate_roi(reference_inputs, reference_parameters)

        # When
        serialized = json.loads(json.dumps(serialize_result(result)))

        # Then
        assert serialized["npv"] == result.npv.value
        assert serialized["irr"] is None
        assert serialized["suppressed"] == {"irr": "irr_not_unique"}
        assert len(serialized["balance"]) == reference_parameters.horizon_years + 1
        assert serialized["basis"]["parameter_set_version"] == "EU-2026.1"

    def test_unavailable_result_has_no_series_and_a_cause_for_every_indicator(
        self, reference_inputs, reference_parameters
    ):
        # Given
        result = calculate_roi(replace(reference_inputs, window_days=0.5), reference_parameters)

        # When
        serialized = serialize_result(result)

        # Then
        assert serialized["unavailable"] == "window_too_short"
        assert serialized["cash_flow"] == []
        assert set(serialized["suppressed"].values()) == {"window_too_short"}
        assert len(serialized["suppressed"]) == 6
