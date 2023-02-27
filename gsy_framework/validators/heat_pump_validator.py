from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.validators.utils import validate_range_limit

HeatPumpSettings = ConstSettings.HeatPumpSettings


class HeatPumpValidator(BaseValidator):
    """Validator class for HeatPump devices."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_energy(**kwargs)
        cls._validate_temp(**kwargs)
        cls._validate_rate(**kwargs)

        cls._check_range(
            name="tank_volume_l", value=kwargs["tank_volume_l"],
            min_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.min,
            max_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.max)

    @classmethod
    def _validate_energy(cls, **kwargs):
        """Validate energy related arguments."""
        cls._check_range(
            name="maximum_power_rating_kW", value=kwargs["maximum_power_rating_kW"],
            min_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
            max_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max)

        if (kwargs["consumption_kW"] is not None and
                kwargs["consumption_profile_uuid"] is not None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "consumption_kW shouldn't be set with consumption_profile_uuid."]})

        if (kwargs["consumption_kW"] is None and
                kwargs["consumption_profile_uuid"] is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "Either consumption_kW or consumption_profile_uuid should be set."]})

        if kwargs["consumption_profile_uuid"] is None:
            cls._check_range(
                name="consumption_kW", value=kwargs["consumption_kW"],
                min_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
                max_value=kwargs["maximum_power_rating_kW"])

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

        if not min_temp_c <= max_temp_c:
            raise GSyDeviceException(
                {"misconfiguration": [
                    "Requirement 'min_temp_C <= max_temp_C' is not met."]})

        if (kwargs["external_temp_C"] is not None and
                kwargs["external_temp_profile_uuid"] is not None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "external_temp_C shouldn't be set with external_temp_profile_uuid."]})

        if (kwargs["external_temp_C"] is None and
                kwargs["external_temp_profile_uuid"] is None):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "Either external_temp_C or external_temp_profile_uuid should be set."]})

        if kwargs["external_temp_profile_uuid"] is None:
            cls._check_range(
                name="external_temp_C", value=kwargs["external_temp_C"],
                min_value=HeatPumpSettings.TEMP_C_LIMIT.min,
                max_value=HeatPumpSettings.TEMP_C_LIMIT.max)

    @classmethod
    def _validate_rate(cls, **kwargs):
        """Validate energy rate related arguments."""
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

    @classmethod
    def _check_range(cls, name, value, min_value, max_value):
        if value is None:
            raise GSyDeviceException(
                {"misconfiguration": [
                    f"Value of {name} should not be None."]})

        validate_range_limit(
            min_value, value, max_value,
            {"misconfiguration": [f"{name} should be between {min_value} & {max_value}."]})
