from gsy_framework.validators.pv_validator import PVValidator


class WindTurbineValidator(PVValidator):
    """Validator class for wind turbine devices."""

    @classmethod
    def validate_energy(cls, **kwargs):
        """Overwrite super method because energy params do not need to be validated."""

    @classmethod
    def validate_settings(cls, **kwargs):
        """Overwrite super method because settings params do not need to be validated."""
