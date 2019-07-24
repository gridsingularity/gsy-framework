
from d3a_interface.constants_limits import Constants, GlobalConfigSetting


def test_constanst():
    assert Constants.GeneralSettings.MIN_RISK == 0
    assert GlobalConfigSetting.DURATION_D == 1
