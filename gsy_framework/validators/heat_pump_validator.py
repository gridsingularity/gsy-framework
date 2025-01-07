from gsy_framework.constants_limits import ConstSettings, GlobalConfig
from gsy_framework.exceptions import GSyDeviceException
from gsy_framework.validators.base_validator import BaseValidator
from gsy_framework.validators.utils import validate_range_limit
from gsy_framework.enums import HeatPumpSourceType

HeatPumpSettings = ConstSettings.HeatPumpSettings


class HeatPumpValidator(BaseValidator):
    """Validator class for HeatPump assets."""

    @classmethod
    def validate(cls, **kwargs):
        cls._validate_temp(**kwargs)
        cls.validate_rate(**kwargs)
        cls._validate_source_type(**kwargs)
        cls._validate_tank_volume(**kwargs)
        cls._validate_profiles(**kwargs)
        cls._validate_max_power(**kwargs)

    @classmethod
    def _validate_profiles(cls, **kwargs):
        """Validate profile arguments."""
        if (
            kwargs.get("consumption_kWh_profile") is None
            and kwargs.get("consumption_kWh_profile_uuid") is None
            and kwargs.get("heat_demand_Q_profile") is None
        ):
            raise GSyDeviceException(
                {
                    "misconfiguration": [
                        "consumption_kWh_profile or heat_demand_Q_profile should be provided."
                    ]
                }
            )

        if (
            kwargs.get("source_temp_C_profile") is None
            and kwargs.get("source_temp_C_profile_uuid") is None
        ):
            raise GSyDeviceException(
                {"misconfiguration": ["source_temp_C_profile should be provided."]}
            )

    @classmethod
    def _validate_max_power(cls, **kwargs):
        """Validate energy related arguments."""

        cls._check_range(
            name="maximum_power_rating_kW",
            value=kwargs["maximum_power_rating_kW"],
            min_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.min,
            max_value=HeatPumpSettings.MAX_POWER_RATING_KW_LIMIT.max,
        )

    @classmethod
    def _validate_temp(cls, **kwargs):
        """Validate temperature related arguments."""
        temperature_arg_names = ["min_temp_C", "max_temp_C", "initial_temp_C"]
        for temperature_arg_name in temperature_arg_names:
            if kwargs.get(temperature_arg_name):
                cls._check_range(
                    name=temperature_arg_name,
                    value=kwargs[temperature_arg_name],
                    min_value=HeatPumpSettings.TEMP_C_LIMIT.min,
                    max_value=HeatPumpSettings.TEMP_C_LIMIT.max,
                )

        min_temp_c = kwargs.get("min_temp_C")
        max_temp_c = kwargs.get("max_temp_C")
        initial_temp_c = kwargs.get("initial_temp_C")
        if min_temp_c is None:
            min_temp_c = HeatPumpSettings.MIN_TEMP_C
        if max_temp_c is None:
            max_temp_c = HeatPumpSettings.MAX_TEMP_C
        if initial_temp_c is None:
            initial_temp_c = HeatPumpSettings.INIT_TEMP_C

        if not min_temp_c <= initial_temp_c <= max_temp_c:
            raise GSyDeviceException(
                {
                    "misconfiguration": [
                        "Requirement 'min_temp_C <= initial_temp_C <= max_temp_C' is not met."
                    ]
                }
            )

    @classmethod
    def validate_rate(cls, **kwargs):
        """Validate energy rate related arguments."""
        if (
            kwargs.get("initial_buying_rate") is None
            and kwargs.get("final_buying_rate") is None
            and kwargs.get("update_interval") is None
        ):
            return

        if kwargs.get("initial_buying_rate") is None or kwargs.get("update_interval") is None:
            raise GSyDeviceException(
                {
                    "misconfiguration": [
                        "All pricing parameters of heat pump should be provided: "
                        "initial_buying_rate, update_interval"
                    ]
                }
            )

        if kwargs.get("update_interval") == 0:
            raise GSyDeviceException({"misconfiguration": ["update_interval should not be zero"]})

        buying_rate_arg_names = ["initial_buying_rate", "preferred_buying_rate"]
        for buying_rate_arg_name in buying_rate_arg_names:
            cls._check_range(
                name=buying_rate_arg_name,
                value=kwargs[buying_rate_arg_name],
                min_value=HeatPumpSettings.BUYING_RATE_LIMIT.initial,
                max_value=HeatPumpSettings.BUYING_RATE_LIMIT.final,
            )

        initial_buying_rate = kwargs["initial_buying_rate"]
        preferred_buying_rate = kwargs["preferred_buying_rate"]
        final_buying_rate = (
            GlobalConfig.MARKET_MAKER_RATE
            if kwargs.get("use_market_maker_rate") is True
            else kwargs.get("final_buying_rate")
        )

        validate_range_limit(
            initial_buying_rate,
            preferred_buying_rate,
            final_buying_rate,
            {
                "misconfiguration": [
                    "Requirement 'initial_buying_rate <= preferred_buying_rate <= "
                    "final_buying_rate' is not met."
                ]
            },
        )

    @staticmethod
    def _validate_source_type(**kwargs):
        if kwargs.get("source_type"):
            try:
                if kwargs["source_type"] is not None:
                    HeatPumpSourceType(kwargs["source_type"])
            except ValueError as ex:
                raise GSyDeviceException(
                    {
                        "misconfiguration": [
                            "HeatPump source type not one of "
                            f"{[st.value for st in HeatPumpSourceType]}"
                        ]
                    }
                ) from ex

    @classmethod
    def _validate_tank_volume(cls, **kwargs):
        if kwargs.get("tank_volume_l"):
            cls._check_range(
                name="tank_volume_l",
                value=kwargs["tank_volume_l"],
                min_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.min,
                max_value=HeatPumpSettings.TANK_VOLUME_L_LIMIT.max,
            )

    @classmethod
    def _check_range(cls, name, value, min_value, max_value):
        if value is None:
            raise GSyDeviceException(
                {"misconfiguration": [f"Value of {name} should not be None."]}
            )

        validate_range_limit(
            min_value,
            value,
            max_value,
            {"misconfiguration": [f"{name} should be between {min_value} & {max_value}."]},
        )


class VirtualHeatPumpValidator(HeatPumpValidator):
    """Validator class for VirtualHeatPump assets."""

    @classmethod
    def validate(cls, **kwargs):
        super().validate(**kwargs)
        cls._check_calibration_coefficient(**kwargs)

    @classmethod
    def _check_calibration_coefficient(cls, **kwargs):
        if kwargs.get("calibration_coefficient") is not None:
            cls._check_range(
                "calibration_coefficient",
                kwargs.get("calibration_coefficient"),
                HeatPumpSettings.CALIBRATION_COEFFICIENT_RANGE.min,
                HeatPumpSettings.CALIBRATION_COEFFICIENT_RANGE.max,
            )

    @classmethod
    def _validate_profiles(cls, **kwargs):
        """Validate profile arguments."""
        if (
            kwargs.get("water_supply_temp_C_profile") is None
            and kwargs.get("water_supply_temp_C_profile_uuid") is None
        ):
            raise GSyDeviceException(
                {"misconfiguration": ["water_supply_temp_C_profile should be provided."]}
            )
        if (
            kwargs.get("water_return_temp_C_profile") is None
            and kwargs.get("water_return_temp_C_profile_uuid") is None
        ):
            raise GSyDeviceException(
                {"misconfiguration": ["water_return_temp_C_profile should be provided."]}
            )
        if (
            kwargs.get("dh_water_flow_m3_profile") is None
            and kwargs.get("dh_water_flow_m3_profile_uuid") is None
        ):
            raise GSyDeviceException(
                {"misconfiguration": ["dh_water_flow_m3_profile should be provided."]}
            )

    @classmethod
    def _validate_energy(cls, **kwargs):
        pass
