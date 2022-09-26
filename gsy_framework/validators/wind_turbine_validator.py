from gsy_framework.constants_limits import ConstSettings
from gsy_framework.validators.pv_validator import PVValidator
from gsy_framework.validators.utils import validate_range_limit

WindTurbineSettings = ConstSettings.PVSettings


class WindTurbineValidator(PVValidator):
    """Validator class for wind turbine devices."""

    @classmethod
    def validate_energy(cls, **kwargs):
        """Validate energy parameter of wind turbine."""
        if kwargs.get("capacity_kW") is not None:
            error_message = {
                "misconfiguration": ["capacity_kW should be in between "
                                     f"{WindTurbineSettings.CAPACITY_KW_LIMIT.min} & "
                                     f"{WindTurbineSettings.CAPACITY_KW_LIMIT.max}"]}
            validate_range_limit(WindTurbineSettings.CAPACITY_KW_LIMIT.min,
                                 kwargs["capacity_kW"],
                                 WindTurbineSettings.CAPACITY_KW_LIMIT.max, error_message)

    @classmethod
    def validate_settings(cls, **kwargs):
        """Overwrite super method because settings params do not need to be validated."""
