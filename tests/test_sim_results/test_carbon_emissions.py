from math import isclose
from unittest.mock import patch

import pytest
import pandas as pd

from gsy_framework.constants_limits import (
    FLOATING_POINT_TOLERANCE,
)
from gsy_framework.sim_results.carbon_emissions.results import (
    CarbonEmissionsHandler,
)
from gsy_framework.sim_results.carbon_emissions.constants import (
    MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES,
    YEARLY_CARBON_EMISSIONS_COUNTRY_CODES,
)
from tests.test_sim_results.constants import (
    TEST_TRADE_PROFILE_RESULTS,
    TEST_IMPORTED_EXPORTED_ENERGY_RESULTS,
)


class TestCarbonEmissionsHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self.trade_profile = TEST_TRADE_PROFILE_RESULTS
        self.imported_exported_energy = TEST_IMPORTED_EXPORTED_ENERGY_RESULTS

    @patch(
        "gsy_framework.sim_results.carbon_emissions.results.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20240101.csv", header=[0, 1], index_col=0
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
        "gsy_framework.sim_results.carbon_emissions.results.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20240101.csv", header=[0, 1], index_col=0
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
        "gsy_framework.sim_results.carbon_emissions.results.EntsoePandasClientAdapter._query_generation_per_plant",  # noqa: E501
        lambda *args: pd.read_csv(
            "tests/static/generation_per_plant_entsoe_BE_20240101.csv", header=[0, 1], index_col=0
        ),
    )
    @pytest.mark.parametrize(
        ("country_code", "expected_carbon_generated_g"),
        list(
            zip(
                MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES + YEARLY_CARBON_EMISSIONS_COUNTRY_CODES,
                [
                    1275.092000,
                    152.852000,
                    170.632000,
                    301.420000,
                    57.064000,
                    475.244000,
                    1008.000000,
                    1624.504000,
                    1296.568000,
                    2050.300000,
                    1148.252000,
                    1092.280000,
                    294.084000,
                    216.160000,
                    301.140000,
                    286.048000,
                    1504.356000,
                    1031.828000,
                    991.956000,
                    1180.704000,
                    958.132000,
                    1.988000,
                    1784.272000,
                    371.084336,
                    1776.910800,
                    1711.111080,
                    489.256208,
                    1711.111080,
                    991.488036,
                    740.706820,
                    1571.428600,
                    1536.338328,
                    1879.889312,
                    1848.276080,
                    2532.920600,
                    1935.951360,
                    1695.412880,
                    632.258088,
                    1635.398240,
                    1822.222192,
                    65.333335,
                    1488.724328,
                    2374.144360,
                    152.852000,
                    1811.764640,
                    2502.956400,
                    1309.091000,
                    700.000056,
                    1169.579936,
                    855.172360,
                    476.119028,
                    1562.790600,
                    1799.999880,
                    0.000000,
                    1759.999920,
                    815.117800,
                    1630.487488,
                    726.631276,
                    1800.000160,
                    1960.000000,
                    700.000000,
                    57.064000,
                    1102.877720,
                    1785.306880,
                    68.478267,
                    1938.461840,
                    1482.353040,
                    1626.183720,
                    1866.666760,
                    420.625912,
                    1596.855512,
                    760.110876,
                    1657.142844,
                    1768.420920,
                    482.758612,
                    69.001290,
                    1400.000000,
                    1133.333404,
                    807.692424,
                    609.900984,
                    1240.000020,
                    1376.470536,
                    1866.666760,
                    469.262892,
                    1355.200084,
                    1680.000168,
                    500.000004,
                    1792.000000,
                    1400.000000,
                    1744.000160,
                    919.149056,
                    663.157936,
                    1750.000000,
                    1792.982520,
                    1588.461560,
                    790.341356,
                    1008.000000,
                    1997.633960,
                    1624.504000,
                    1834.349832,
                    1928.679088,
                    1555.555512,
                    1148.252000,
                    1514.586220,
                    2299.894520,
                    197.377057,
                    1866.666760,
                ],
            )
        ),
    )
    def test_carbon_emissions_handles_different_country_codes_correctly(
        self, country_code, expected_carbon_generated_g
    ):
        # Given
        energy_handler = CarbonEmissionsHandler(entsoe_api_key="false_key")

        # When
        carbon_emissions = energy_handler.calculate_from_gsy_trade_profile(
            country_code=country_code, trade_profile=self.trade_profile
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_g"],
            expected_carbon_generated_g,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
