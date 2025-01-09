from math import isclose

from unittest.mock import patch
import pandas as pd

from gsy_framework.constants_limits import (
    FLOATING_POINT_TOLERANCE,
)
from gsy_framework.sim_results.carbon_emissions import CarbonEmissionsHandler

from .constants import TEST_TRADE_PROFILE_RESULTS


class TestCarbonEmissionsHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self.results_list = TEST_TRADE_PROFILE_RESULTS

    @patch(
        "gsy_framework.sim_results.carbon_emissions.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20210801.csv", header=[0, 1], index_col=0
        ),
    )
    def test_carbon_emissions_from_gsy_trade_profile_calculates_correctly(
        self,
    ):
        # Given
        energy_handler = CarbonEmissionsHandler(entsoe_api_key="false_key")

        # When
        carbon_emissions = energy_handler.calculate_carbon_emissions_from_gsy_trade_profile(
            country_code="BE", trade_profile=self.results_list
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_g"], 3.41924, abs_tol=FLOATING_POINT_TOLERANCE
        )
