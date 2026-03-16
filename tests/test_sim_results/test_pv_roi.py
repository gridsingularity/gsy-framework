from math import isclose

from gsy_framework.constants_limits import (
    FLOATING_POINT_TOLERANCE,
)
from gsy_framework.sim_results.pv_roi import (
    PVROI,
)
from tests.test_sim_results.constants import (
    TEST_AREA_SETUP_PV_ONLY,
)


class TestPVROI:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self.area_setup = TEST_AREA_SETUP_PV_ONLY

    def test_carbon_emissions_from_gsy_trade_profile_calculates_correctly(
        self,
    ):
        # Given
        pv_roi = PVROI()

        # When
        pv_roi = pv_roi.process_area(area=self.area_setup)

        # Then
        # assert isclose(
        #     carbon_emissions["carbon_generated_g"], 417.004, abs_tol=FLOATING_POINT_TOLERANCE
        # )
