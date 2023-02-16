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
            name="tank_volume_l", value=kwargs.get("tank_volume_l"),
            _min=HeatPumpSettings.TANK_VOLUME_L_LIMIT.min,
            _max=HeatPumpSettings.TANK_VOLUME_L_LIMIT.max)

        if kwargs.get("external_temp_C") and kwargs.get("external_temp_profile_uuid"):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "external_temp_C shouldn't be set with external_temp_profile_uuid."]})

        if kwargs.get("consumption_kW") and kwargs.get("consumption_profile_uuid"):
            raise GSyDeviceException(
                {"misconfiguration": [
                    "consumption_kW shouldn't be set with consumption_profile_uuid."]})

    @classmethod
    def _validate_energy(cls, **kwargs):
        """Validate energy related arguments."""
        cls._check_range(
            name="maximum_power_rating_kW", value=kwargs.get("maximum_power_rating_kW"),
            _min=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
            _max=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max)

    @classmethod
    def _validate_temp(cls, **kwargs):
        """Validate temperature related arguments."""
        temperature_arg_names = [
            "min_temp_C", "max_temp_C", "initial_temp_C", "external_temp_C"]
        for temperature_arg_name in temperature_arg_names:
            cls._check_range(
                name=temperature_arg_name, value=kwargs.get(temperature_arg_name),
                _min=HeatPumpSettings.TEMP_C_LIMIT.min,
                _max=HeatPumpSettings.TEMP_C_LIMIT.max)

        min_temp_c = kwargs.get("min_temp_C", HeatPumpSettings.MIN_TEMP_C.value)
        max_temp_c = kwargs.get("max_temp_C", HeatPumpSettings.MAX_TEMP_C.value)
        initial_temp_c = kwargs.get("initial_temp_C", HeatPumpSettings.INIT_TEMP_C.value)
        validate_range_limit(
            min_temp_c, initial_temp_c, max_temp_c,
            {"misconfiguration": [
                "Requirement 'min_temp_C <= initial_temp_C <= max_temp_C' not met."
            ]})

    @classmethod
    def _validate_rate(cls, **kwargs):
        """Validate energy rate related arguments."""
        buying_rate_arg_names = [
            "initial_buying_rate", "preferred_buying_rate", "final_buying_rate"]
        for buying_rate_arg_name in buying_rate_arg_names:
            cls._check_range(
                name=buying_rate_arg_name, value=kwargs.get(buying_rate_arg_name),
                _min=HeatPumpSettings.TEMP_C_LIMIT.min,
                _max=HeatPumpSettings.TEMP_C_LIMIT.max)

        initial_buying_rate = kwargs.get(
            "initial_buying_rate", HeatPumpSettings.BUYING_RATE_RANGE.min)
        preferred_buying_rate = kwargs.get(
            "preferred_buying_rate", HeatPumpSettings.PREFERRED_BUYING_RATE.value)
        final_buying_rate = kwargs.get(
            "final_buying_rate", HeatPumpSettings.BUYING_RATE_RANGE.max)

        validate_range_limit(
            initial_buying_rate, preferred_buying_rate, final_buying_rate,
            {"misconfiguration": [
                "Requirement "
                "'initial_buying_rate <= preferred_buying_rate <= final_buying_rate' not met."
            ]})

    @classmethod
    def _check_range(cls, name, value, _min, _max):
        if value is None:
            return

        validate_range_limit(
            HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min, value,
            HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max,
            {"misconfiguration": [f"{name} should be between {_min} & {_max}."]})
