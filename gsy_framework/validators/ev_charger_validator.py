from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.enums import GridIntegrationType
from gsy_framework.validators.utils import validate_range_limit

EVChargerSettings = ConstSettings.EVChargerSettings


class EVChargerValidator(BaseValidator):
    """Validator class for EV Charger assets."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_grid_integration(**kwargs)
        cls._validate_max_power(**kwargs)

    @staticmethod
    def _validate_grid_integration(**kwargs):
        if kwargs.get("grid_integration"):
            try:
                if kwargs["grid_integration"] is not None:
                    GridIntegrationType(kwargs["grid_integration"])
            except ValueError as ex:
                raise GSyDeviceException(
                    {
                        "misconfiguration": [
                            "EV Charger grid integration not one of "
                            f"{[st.value for st in GridIntegrationType]}"
                        ]
                    }
                ) from ex

    @classmethod
    def _validate_max_power(cls, **kwargs):
        """Validate energy related arguments."""
        name = "maximum_power_rating_kW"
        value = kwargs.get("maximum_power_rating_kW")
        min_limit = EVChargerSettings.MAX_POWER_RATING_KW_LIMIT.min
        max_limit = EVChargerSettings.MAX_POWER_RATING_KW_LIMIT.max
        if value is None:
            raise GSyDeviceException(
                {"misconfiguration": [f"Value of {name} should not be None."]}
            )

        validate_range_limit(
            min_limit,
            value,
            max_limit,
            {"misconfiguration": [f"{name} should be between {min_limit} & {max_limit}."]},
        )
