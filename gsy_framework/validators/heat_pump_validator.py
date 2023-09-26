from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.validators.utils import validate_range_limit
from gsy_framework.enums import HeatPumpSourceType

HeatPumpSettings = ConstSettings.HeatPumpSettings


class HeatPumpValidator(BaseValidator):
    """Validator class for HeatPump devices."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_energy(**kwargs)
        cls._validate_temp(**kwargs)
        cls.validate_rate(**kwargs)
        cls._validate_source_type(**kwargs)
        cls._validate_tank_volume(**kwargs)

    @classmethod
    def _validate_energy(cls, **kwargs):
        """Validate energy related arguments."""
        if kwargs.get("maximum_power_rating_kW"):
            cls._check_range(
                name="maximum_power_rating_kW", value=kwargs.get("maximum_power_rating_kW"),
                min_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
                max_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max)
        if (kwargs.get("consumption_kWh_profile") is None and
                kwargs.get("consumption_kWh_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "consumption_kWh_profile should be provided."]})

    @classmethod
    def _validate_temp(cls, **kwargs):
        """Validate temperature related arguments."""
        temperature_arg_names = [
            "min_temp_C", "max_temp_C", "initial_temp_C"]
        for temperature_arg_name in temperature_arg_names:
            if kwargs.get(temperature_arg_name):
                cls._check_range(
                    name=temperature_arg_name, value=kwargs[temperature_arg_name],
                    min_value=HeatPumpSettings.TEMP_C_LIMIT.min,
                    max_value=HeatPumpSettings.TEMP_C_LIMIT.max)

        if kwargs.get("min_temp_C") and kwargs.get("max_temp_C"):
            if not kwargs["min_temp_C"] <= kwargs["max_temp_C"]:
                raise GSyDeviceException(
                    {"misconfiguration": [
                        "Requirement 'min_temp_C <= max_temp_C' is not met."]})

        if (kwargs.get("external_temp_C_profile") is None and
                kwargs.get("external_temp_C_profile_uuid") is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "external_temp_C_profile should be provided."]})

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate energy rate related arguments."""
        if not(kwargs.get("initial_buying_rate")
               and kwargs.get("final_buying_rate")
               and kwargs.get("update_interval")):
            return
        if (not kwargs.get("initial_buying_rate")
                or not kwargs.get("final_buying_rate")
                or not kwargs.get("update_interval")):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "All pricing parameters of heat pump should be provided:"
                    "initial_buying_rate, final_buying_rate, update_interval"]})

        buying_rate_arg_names = [
            "initial_buying_rate", "preferred_buying_rate", "final_buying_rate"]
        for buying_rate_arg_name in buying_rate_arg_names:
            cls._check_range(
                name=buying_rate_arg_name, value=kwargs[buying_rate_arg_name],
                min_value=HeatPumpSettings.TEMP_C_LIMIT.min,
                max_value=HeatPumpSettings.TEMP_C_LIMIT.max)

        initial_buying_rate = kwargs["initial_buying_rate"]
        preferred_buying_rate = kwargs["preferred_buying_rate"]
        final_buying_rate = kwargs["final_buying_rate"]

        validate_range_limit(
            initial_buying_rate, preferred_buying_rate, final_buying_rate,
            {"misconfiguration": [
                "Requirement "
                "'initial_buying_rate <= preferred_buying_rate <= final_buying_rate' is not met."
            ]})

    @staticmethod
    def _validate_source_type(**kwargs):
        if kwargs.get("source_type"):
            allowed_source_type_ints = [st.value for st in HeatPumpSourceType]
            if kwargs.get("source_type") not in allowed_source_type_ints:
                raise GSyDeviceException(
                    {"misconfiguration": [
                        f"HeatPump source type not one of {allowed_source_type_ints}"]})

    @classmethod
    def _validate_tank_volume(cls, **kwargs):
        if kwargs.get("tank_volume_l"):
            cls._check_range(
                name="tank_volume_l", value=kwargs["tank_volume_l"],
                min_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.min,
                max_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.max)

    @classmethod
    def _check_range(cls, name, value, min_value, max_value):
        if value is None:
            raise GSyDeviceException(
                {"misconfiguration": [
                    f"Value of {name} should not be None."]})

        validate_range_limit(
            min_value, value, max_value,
            {"misconfiguration": [f"{name} should be between {min_value} & {max_value}."]})
