from math import isclose

from unittest.mock import patch
import pandas as pd
from pendulum import duration

from gsy_framework.constants_limits import (
    FLOATING_POINT_TOLERANCE,
)
from gsy_framework.sim_results.carbon_emissions import CarbonEmissionsHandler

from .constants import TEST_COEFFICIENT_AREA_RESULTS


class TestCarbonEmissionsHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self.results_list = TEST_COEFFICIENT_AREA_RESULTS
        self.community_uuid = "7b359ad5-a9b4-47c6-a147-85a7ee8e5dd1"
        self.house1_uuid = "cf1f5882-ec59-4506-8801-e3b5f7aaf408"
        self.house2_uuid = "1521b3f4-c655-4ab8-b8b7-94f14f7279a0"

    @patch(
        "gsy_framework.sim_results.carbon_emissions.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv("tests/static/generation_per_plant_entsoe_BE_20210801.csv"),
    )
    def test_update_calculates_carbon_emissions_correctly(self):
        energy_handler = CarbonEmissionsHandler(api_key="false_key")
        energy_handler.update(
            country_code="BE", time_slot=duration(minutes=15), results_list=self.results_list
        )

        community_carbon_generated_g = self.results_list[0]["results"][self.community_uuid][
            "carbon_generated_g"
        ]
        communtiy_carbon_savings_g = self.results_list[0]["results"][self.community_uuid][
            "carbon_savings_g"
        ]
        house1_carbon_generated_g = self.results_list[0]["results"][self.house1_uuid][
            "carbon_generated_g"
        ]
        house1_carbon_savings_g = self.results_list[0]["results"][self.house1_uuid][
            "carbon_savings_g"
        ]
        assert isclose(community_carbon_generated_g, 1.26469, abs_tol=FLOATING_POINT_TOLERANCE)
        assert isclose(communtiy_carbon_savings_g, 0.18471, abs_tol=FLOATING_POINT_TOLERANCE)
        assert isclose(house1_carbon_generated_g, 0.0, abs_tol=FLOATING_POINT_TOLERANCE)
        assert isclose(house1_carbon_savings_g, 0.0, abs_tol=FLOATING_POINT_TOLERANCE)
