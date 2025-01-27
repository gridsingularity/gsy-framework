from math import isclose
from unittest.mock import patch

import pytest
import pandas as pd

from gsy_framework.constants_limits import (
    FLOATING_POINT_TOLERANCE,
)
from gsy_framework.sim_results.carbon_emissions import (
    CarbonEmissionsHandler,
    MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES,
)

from .constants import TEST_TRADE_PROFILE_RESULTS, TEST_IMPORTED_EXPORTED_ENERGY_RESULTS


class TestCarbonEmissionsHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self.trade_profile = TEST_TRADE_PROFILE_RESULTS
        self.imported_exported_energy = TEST_IMPORTED_EXPORTED_ENERGY_RESULTS

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
        carbon_emissions = energy_handler.calculate_from_gsy_trade_profile(
            country_code="BE", trade_profile=self.trade_profile
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_g"], 87.50675385, abs_tol=FLOATING_POINT_TOLERANCE
        )

    @patch(
        "gsy_framework.sim_results.carbon_emissions.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20210801.csv", header=[0, 1], index_col=0
        ),
    )
    def test_carbon_emissions_from_gsy_imported_exported_energy_calculates_correctly(
        self,
    ):
        # Given
        energy_handler = CarbonEmissionsHandler(entsoe_api_key="false_key")

        # When
        carbon_emissions = energy_handler.calculate_from_gsy_imported_exported_energy(
            country_code="BE", imported_exported_energy=self.imported_exported_energy
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_base_case_g"],
            32.60368649,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
        assert isclose(
            carbon_emissions["carbon_generated_gsy_g"],
            13.58486937,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
        assert isclose(
            carbon_emissions["carbon_savings_g"],
            19.01881711,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )

    @patch(
        "gsy_framework.sim_results.carbon_emissions.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20210801.csv", header=[0, 1], index_col=0
        ),
    )
    @pytest.mark.parametrize(
        "country_code",
        MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES
        + [  # Monthly + Yearly Country codes
            "ET",
            "GF",
            "PF",
            "GH",
            "GI",
            "GL",
            "GD",
            "GP",
            "GU",
            "GT",
            "GN",
            "GW",
            "GY",
            "HT",
            "HN",
            "IR",
            "IQ",
        ],
    )
    def test_carbon_emissions_handles_different_country_codes_correctly(self, country_code):
        # Given
        energy_handler = CarbonEmissionsHandler(entsoe_api_key="false_key")

        # When
        carbon_emissions = energy_handler.calculate_from_gsy_trade_profile(
            country_code=country_code, trade_profile=self.trade_profile
        )

        # Then
        assert carbon_emissions["carbon_generated_g"] > 0
