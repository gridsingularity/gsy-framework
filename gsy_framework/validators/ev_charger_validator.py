from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.enums import GridIntegrationType

EVChargerSettings = ConstSettings.EVChargerSettings


class EVChargerValidator(BaseValidator):
    """Validator class for EV Charger assets."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_grid_integration(**kwargs)

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

        cls._check_range(
            name="maximum_power_rating_kW",
            value=kwargs["maximum_power_rating_kW"],
            min_value=EVChargerSettings.MAX_POWER_RATING_KW_LIMIT.min,
            max_value=EVChargerSettings.MAX_POWER_RATING_KW_LIMIT.max,
        )
