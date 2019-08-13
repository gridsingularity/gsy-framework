
from d3a_interface.constants_limits import ConstSettings, GlobalConfig


def test_constanst():
    assert ConstSettings.GeneralSettings.MIN_RISK == 0
    assert GlobalConfig.DURATION_D == 1
