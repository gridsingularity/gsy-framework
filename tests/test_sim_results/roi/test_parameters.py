from gsy_framework.sim_results.roi.parameters import DEFAULT_PARAMETER_SET, EU_2026_1


class TestPublishedParameterSets:

    def test_eu_2026_1_matches_the_reference_model(self, reference_parameters):
        # Given / When / Then
        assert EU_2026_1 == reference_parameters

    def test_default_is_eu_2026_1(self):
        # Given / When / Then
        assert DEFAULT_PARAMETER_SET is EU_2026_1
