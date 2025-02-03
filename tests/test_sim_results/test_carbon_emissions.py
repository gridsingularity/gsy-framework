from math import isclose

import pytest

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

    def test_carbon_emissions_from_gsy_trade_profile_calculates_correctly(
        self,
    ):
        # Given
        energy_handler = CarbonEmissionsHandler()

        # When
        carbon_emissions = energy_handler.calculate_from_gsy_trade_profile(
            country_code="BE", trade_profile=self.trade_profile
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_g"], 417.004, abs_tol=FLOATING_POINT_TOLERANCE
        )

    def test_carbon_emissions_from_gsy_imported_exported_energy_calculates_correctly(
        self,
    ):
        # Given
        energy_handler = CarbonEmissionsHandler()

        # When
        carbon_emissions = energy_handler.calculate_from_gsy_imported_exported_energy(
            country_code="BE", imported_exported_energy=self.imported_exported_energy
        )

        # Then
        assert isclose(
            carbon_emissions["carbon_generated_base_case_g"],
            178.716,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
        assert isclose(
            carbon_emissions["carbon_generated_gsy_g"],
            74.465,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )
        assert isclose(
            carbon_emissions["carbon_savings_g"],
            104.251,
            abs_tol=FLOATING_POINT_TOLERANCE,
        )

    @pytest.mark.parametrize(
        ("country_code", "expected_carbon_generated_g"),
        list(
            zip(
                MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES + YEARLY_CARBON_EMISSIONS_COUNTRY_CODES,
                [
                    611.044,
                    1339.716,
                    1216.264,
                    417.004,
                    1338.0080000000003,
                    97.07599999999998,
                    108.35999999999999,
                    280.36400000000003,
                    404.45999999999987,
                    124.06799999999997,
                    2219.1400000000003,
                    1416.2680000000003,
                    1149.2040000000002,
                    357.952,
                    987.6999999999997,
                    262.6120000000001,
                    238.44800000000006,
                    174.804,
                    585.032,
                    369.7679999999999,
                    1083.46,
                    1008.0,
                    661.3320000000001,
                    709.5200000000002,
                    1624.5040000000006,
                    844.1159999999999,
                    1299.8160000000005,
                    2023.28,
                    0.0,
                    929.2079999999997,
                    1183.3080000000002,
                    1112.412,
                    316.7919999999999,
                    781.3399999999999,
                    370.4119999999999,
                    378.952,
                    702.7719999999999,
                    39.70399999999999,
                    132.46800000000002,
                    714.7559999999999,
                    347.564,
                    1531.236,
                    2151.884000000001,
                    177.35200000000006,
                    762.804,
                    1235.3040000000003,
                    11.508,
                    1042.888,
                    621.3760000000001,
                    817.4599999999999,
                    1211.5320000000002,
                    1199.1839999999997,
                    962.6120000000004,
                    320.516,
                    1752.4919999999993,
                    371.0843360000001,
                    1776.9107999999999,
                    1711.1110800000006,
                    489.25620799999996,
                    1711.1110800000006,
                    991.4880359999999,
                    740.7068200000001,
                    1571.4285999999997,
                    1536.3383280000005,
                    1879.8893120000005,
                    1848.27608,
                    2532.9206000000004,
                    1935.95136,
                    1695.4128800000003,
                    632.258088,
                    1635.3982399999995,
                    1822.2221919999993,
                    65.33333520000001,
                    1488.724328,
                    2374.1443600000002,
                    97.07599999999998,
                    1811.7646399999996,
                    2502.9564,
                    1309.091,
                    700.000056,
                    1169.579936,
                    855.1723600000004,
                    476.1190280000001,
                    1562.7905999999996,
                    1799.9998799999998,
                    0.0,
                    1759.9999199999997,
                    815.1178000000003,
                    1630.4874880000007,
                    726.6312760000002,
                    1800.0001599999998,
                    1960.0,
                    700.0,
                    124.06799999999997,
                    1102.87772,
                    1785.3068799999996,
                    68.4782672,
                    1938.4618399999997,
                    1482.3530400000006,
                    1626.18372,
                    1866.6667599999994,
                    420.62591200000014,
                    1596.8555119999992,
                    760.110876,
                    1657.142844,
                    1768.4209199999996,
                    482.7586119999999,
                ],
            )
        ),
    )
    def test_carbon_emissions_handles_different_country_codes_correctly(
        self, country_code, expected_carbon_generated_g
    ):
        # Given
        energy_handler = CarbonEmissionsHandler()

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
