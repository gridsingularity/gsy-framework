from gsy_framework.constants_limits import ConstSettings, GlobalConfig
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.validators.utils import validate_range_limit

HeatPumpSettings = ConstSettings.HeatPumpSettings


class HeatPumpValidator(BaseValidator):
    """Validator class for HeatPump assets."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_energy(**kwargs)
        cls._validate_temp(**kwargs)
        cls.validate_rate(**kwargs)
        cls._validate_profiles(**kwargs)

        cls._check_range(
            name="tank_volume_l", value=kwargs["tank_volume_l"],
            min_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.min,
            max_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.max)

    @classmethod
    def _validate_profiles(cls, **kwargs):
        """Validate profile arguments."""
        if (kwargs.get("consumption_kWh_profile") is None and
                kwargs.get("consumption_kWh_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "consumption_kWh_profile should be provided."]})

        if (kwargs.get("external_temp_C_profile") is None and
                kwargs.get("external_temp_C_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "external_temp_C_profile should be provided."]})

    @classmethod
    def _validate_energy(cls, **kwargs):
        """Validate energy related arguments."""
        cls._check_range(
            name="maximum_power_rating_kW", value=kwargs["maximum_power_rating_kW"],
            min_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
            max_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max)

    @classmethod
    def _validate_temp(cls, **kwargs):
        """Validate temperature related arguments."""
        temperature_arg_names = [
            "min_temp_C", "max_temp_C", "initial_temp_C"]
        for temperature_arg_name in temperature_arg_names:
            cls._check_range(
                name=temperature_arg_name, value=kwargs[temperature_arg_name],
                min_value=HeatPumpSettings.TEMP_C_LIMIT.min,
                max_value=HeatPumpSettings.TEMP_C_LIMIT.max)

        min_temp_c = kwargs["min_temp_C"]
        max_temp_c = kwargs["max_temp_C"]
        initial_temp_c = kwargs["initial_temp_C"]

        if not min_temp_c <= initial_temp_c <= max_temp_c:
            raise GSyDeviceException(
                {"misconfiguration": [
                    "Requirement 'min_temp_C <= initial_temp_C <= max_temp_C' is not met."]})

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate energy rate related arguments."""
        if not(kwargs.get("initial_buying_rate")
               and kwargs.get("final_buying_rate")
               and kwargs.get("update_interval")):
            return
        if (kwargs.get("initial_buying_rate") is None
                or kwargs.get("update_interval") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "All pricing parameters of heat pump should be provided:"
                    "initial_buying_rate, update_interval"]})

        if kwargs.get("update_interval") == 0:
            raise GSyDeviceException(
                {"misconfiguration": ["update_interval should not be zero"]})

        buying_rate_arg_names = [
            "initial_buying_rate", "preferred_buying_rate"]
        for buying_rate_arg_name in buying_rate_arg_names:
            cls._check_range(
                name=buying_rate_arg_name, value=kwargs[buying_rate_arg_name],
                min_value=HeatPumpSettings.BUYING_RATE_LIMIT.initial,
                max_value=HeatPumpSettings.BUYING_RATE_LIMIT.final)

        initial_buying_rate = kwargs["initial_buying_rate"]
        preferred_buying_rate = kwargs["preferred_buying_rate"]
        final_buying_rate = (
            kwargs.get("final_buying_rate") if kwargs.get("final_buying_rate")
            else GlobalConfig.MARKET_MAKER_RATE)

        validate_range_limit(
            initial_buying_rate, preferred_buying_rate, final_buying_rate,
            {"misconfiguration": [
                "Requirement "
                "'initial_buying_rate <= preferred_buying_rate <= final_buying_rate' is not met."
            ]})

    @classmethod
    def _check_range(cls, name, value, min_value, max_value):
        if value is None:
            raise GSyDeviceException(
                {"misconfiguration": [
                    f"Value of {name} should not be None."]})

        validate_range_limit(
            min_value, value, max_value,
            {"misconfiguration": [f"{name} should be between {min_value} & {max_value}."]})


class VirtualHeatPumpValidator(HeatPumpValidator):
    """Validator class for VirtualHeatPump assets."""

    @classmethod
    def _validate_profiles(cls, **kwargs):
        """Validate profile arguments."""
        if (kwargs.get("water_supply_temp_C_profile") is None and
                kwargs.get("water_supply_temp_C_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "water_supply_temp_C_profile should be provided."]})
        if (kwargs.get("water_return_temp_C_profile") is None and
                kwargs.get("water_return_temp_C_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "water_return_temp_C_profile should be provided."]})
        if (kwargs.get("dh_water_flow_m3_profile") is None and
                kwargs.get("dh_water_flow_m3_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "dh_water_flow_m3_profile should be provided."]})
