from copy import copy

import pytest

from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.heat_pump_validator import (
    HeatPumpValidator,
    VirtualHeatPumpValidator,
)

_params = {
    "min_temp_C": 10,
    "max_temp_C": 70,
    "initial_temp_C": 30,
    "maximum_power_rating_kW": 10,
    "initial_buying_rate": 20,
    "final_buying_rate": 30,
    "update_interval": 1,
    "preferred_buying_rate": 25,
    "tank_volume_l": 500,
}
_hp_params = {
    **_params,
    "source_temp_C_profile": {},
    "source_temp_C_profile_uuid": "1234",
    "consumption_kWh_profile": {},
    "consumption_kWh_profile_uuid": "4321",
}
_virtual_hp_params = {
    **_params,
    "water_supply_temp_C_profile": {},
    "water_supply_temp_C_profile_uuid": "1234",
    "water_return_temp_C_profile": {},
    "water_return_temp_C_profile_uuid": "4321",
    "dh_water_flow_m3_profile": {},
    "dh_water_flow_m3_profile_uuid": "4321",
}


class TestHeatpumpValidator:

    @staticmethod
    @pytest.mark.parametrize(
        "hp_validator_class, hp_params, ",
        [(HeatPumpValidator, _hp_params), (VirtualHeatPumpValidator, _virtual_hp_params)],
    )
    def test_heatpump_validator_succeeds(hp_validator_class, hp_params):
        hp_validator_class().validate(**hp_params)

    @staticmethod
    @pytest.mark.parametrize(
        "hp_validator_class, hp_params, ",
        [(HeatPumpValidator, _hp_params), (VirtualHeatPumpValidator, _virtual_hp_params)],
    )
    def test_heatpump_validator_checks_temp_power_params(hp_validator_class, hp_params):
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "min_temp_C": -10})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "max_temp_C": -10})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "initial_temp_C": -10})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "initial_temp_C": 80})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "min_temp_C": 50, "max_temp_C": 50})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "min_temp_C": 80})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "max_temp_C": 5})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "initial_temp_C": 9})
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "initial_temp_C": 71})

        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "tank_volume_l": -1})

        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**{**hp_params, "maximum_power_rating_kW": -10})

    @staticmethod
    @pytest.mark.parametrize(
        "hp_validator_class, hp_params, ",
        [(HeatPumpValidator, _hp_params), (VirtualHeatPumpValidator, _virtual_hp_params)],
    )
    def test_heatpump_validator_checks_price_params(hp_validator_class, hp_params):
        hp_validator_class().validate(**{**hp_params})

        wrong_price_params = copy(hp_params)
        wrong_price_params["initial_buying_rate"] = 0
        wrong_price_params["update_interval"] = 0  # not allowed value
        with pytest.raises(GSyDeviceException):
            hp_validator_class().validate(**wrong_price_params)

        for none_param_key in ["update_interval", "initial_buying_rate"]:
            wrong_price_params[none_param_key] = None
            with pytest.raises(GSyDeviceException):
                hp_validator_class().validate(**wrong_price_params)

    @staticmethod
    def test_heatpump_validator_checks_profile_params():
        with pytest.raises(GSyDeviceException):
            HeatPumpValidator().validate(
                **{**_hp_params, "source_temp_C_profile": None, "source_temp_C_profile_uuid": None}
            )

        with pytest.raises(GSyDeviceException):
            HeatPumpValidator().validate(
                **{
                    **_hp_params,
                    "consumption_kWh_profile": None,
                    "consumption_kWh_profile_uuid": None,
                }
            )

    @staticmethod
    @pytest.mark.parametrize(
        "wrong_profile_params",
        [
            {"water_supply_temp_C_profile": None, "water_supply_temp_C_profile_uuid": None},
            {"water_return_temp_C_profile": None, "water_return_temp_C_profile_uuid": None},
            {"dh_water_flow_m3_profile": None, "dh_water_flow_m3_profile_uuid": None},
        ],
    )
    def test_virtual_heatpump_validator_checks_profile_params(wrong_profile_params):
        with pytest.raises(GSyDeviceException):
            wrong_vhp_params = {**_virtual_hp_params}
            wrong_vhp_params.update(wrong_profile_params)
            VirtualHeatPumpValidator().validate(**wrong_vhp_params)

    @staticmethod
    def test_virtual_heatpump_validator_checks_calibration_coefficient():
        with pytest.raises(GSyDeviceException):
            VirtualHeatPumpValidator().validate(
                **{**_virtual_hp_params, "calibration_coefficient": -1}
            )

        with pytest.raises(GSyDeviceException):
            VirtualHeatPumpValidator().validate(
                **{**_virtual_hp_params, "calibration_coefficient": 2}
            )

        VirtualHeatPumpValidator().validate(**{**_virtual_hp_params, "calibration_coefficient": 1})
        VirtualHeatPumpValidator().validate(**{**_virtual_hp_params, "calibration_coefficient": 0})
