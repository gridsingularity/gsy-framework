from gsy_framework.constants_limits import ConstSettings
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.enums import GridIntegrationType
from gsy_framework.validators.utils import validate_range_limit
from gsy_framework.read_user_profile import read_arbitrary_profile, InputProfileTypes

EVChargerSettings = ConstSettings.EVChargerSettings


class EVChargerValidator(BaseValidator):
    """Validator class for EV Charger assets."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_grid_integration(**kwargs)
        cls._validate_max_power(**kwargs)
        cls._validate_preferred_charging_power(**kwargs)

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

    @classmethod
    def _validate_preferred_charging_power(cls, **kwargs):
        """Validate preferred charging power parameter."""
        preferred_charging_power = kwargs.get("preferred_charging_power")
        maximum_power_rating_kW = kwargs.get("maximum_power_rating_kW")

        if preferred_charging_power is None:
            return

        # Convert to profile if needed
        preferred_power_profile = read_arbitrary_profile(
            InputProfileTypes.IDENTITY, preferred_charging_power
        )

        # Validate that all absolute values are within maximum power rating
        for time_slot, power_value in preferred_power_profile.items():
            if maximum_power_rating_kW and abs(power_value) > maximum_power_rating_kW:
                raise GSyDeviceException(
                    {
                        "misconfiguration": [
                            f"Absolute value of preferred_charging_power ({abs(power_value)} kW "
                            f"at {time_slot}) cannot exceed maximum_power_rating_kW "
                            f"({maximum_power_rating_kW} kW)."
                        ]
                    }
                )
