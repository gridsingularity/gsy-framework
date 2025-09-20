from enum import Enum
from typing import List

from pendulum import duration


class BidOfferMatchAlgoEnum(Enum):
    """Matching algorithms supported by the GSY exchange."""

    PAY_AS_BID = 1
    PAY_AS_CLEAR = 2
    EXTERNAL = 3
    DOF = 4


class SpotMarketTypeEnum(Enum):
    """Types of markets supported by the GSY exchange."""

    NO_MARKET = 0
    ONE_SIDED = 1
    TWO_SIDED = 2
    COEFFICIENTS = 3


class CoefficientAlgorithm(Enum):
    """Coefficient algorithms supported by the GSY exchange."""

    STATIC = 1
    DYNAMIC = 2
    NO_COMMUNITY_SELF_CONSUMPTION = 3
    LIVE_STREAM = 4


class CloudCoverage(Enum):
    """Available cloud coverage options for PV assets."""

    CLEAR = 0
    PARTIAL_CLOUD = 1
    CLOUDY = 2
    GAUSSIAN = 3
    UPLOAD_PROFILE = 4
    LOCAL_GENERATION_PROFILE = 5  # Generate profiles using Rebase API


class AvailableMarketTypes(Enum):
    """Collection of available market types."""

    SPOT = 0
    BALANCING = 1
    SETTLEMENT = 2
    FUTURE = 3
    DAY_FORWARD = 4
    WEEK_FORWARD = 5
    MONTH_FORWARD = 6
    YEAR_FORWARD = 7
    INTRADAY = 8


class AggregationResolution(Enum):
    """Available aggregation resolutions for forward markets."""

    RES_15_MINUTES = 0
    RES_1_HOUR = 1
    RES_1_WEEK = 2
    RES_1_MONTH = 3
    RES_1_YEAR = 4

    def duration(self):
        """Get duration object based on resolution."""
        return {
            self.RES_15_MINUTES: duration(minutes=15),
            self.RES_1_HOUR: duration(hours=1),
            self.RES_1_WEEK: duration(weeks=1),
            self.RES_1_MONTH: duration(months=1),
            self.RES_1_YEAR: duration(years=1),
        }[self]


class ConfigurationType(Enum):
    """Available configuration types"""

    SIMULATION = 0
    COLLABORATION = 1
    CANARY_NETWORK = 2
    B2B = 3


class HeatPumpSourceType(Enum):
    """Available HeatPump types"""

    AIR = 0
    GROUND = 1


class GridIntegrationType(Enum):
    """Selection of grid integration types for EV chargers.

    - Unidirectional: The charger can only charge EVs, even if the connected EV supports bidirectional charging.
    - Bidirectional: The charger can both charge and discharge, provided the connected EV supports bidirectional charging.
    """

    UNIDIRECTIONAL = 0
    BIDIRECTIONAL = 1


class SCMPropertyType(Enum):
    """Enum for SCM fee types"""

    PER_KWH_FEES = 0
    MONTHLY_FEES = 1
    GRID_FEES = 2
    AREA_PROPERTIES = 3
    PERCENTAGE_FEES = 4

    @classmethod
    def member_names(cls) -> List:
        """Return list of member names."""
        return [e.name for e in cls]


SCM_PROPERTY_TYPE_MAPPING = {
    "taxes_surcharges": SCMPropertyType.PER_KWH_FEES,
    "electricity_tax": SCMPropertyType.PERCENTAGE_FEES,
    "fixed_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "marketplace_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "assistance_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "service_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "contracted_power_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "contracted_power_cargo_monthly_fee": SCMPropertyType.MONTHLY_FEES,
    "energy_cargo_fee": SCMPropertyType.PER_KWH_FEES,
    "grid_import_fee_const": SCMPropertyType.GRID_FEES,
    "grid_export_fee_const": SCMPropertyType.GRID_FEES,
    "coefficient_percentage": SCMPropertyType.AREA_PROPERTIES,
    "market_maker_rate": SCMPropertyType.AREA_PROPERTIES,
    "feed_in_tariff": SCMPropertyType.AREA_PROPERTIES,
}


class SCMSelfConsumptionType(Enum):
    """Self consumption type for SCM algorithm."""

    SIMPLIFIED_COLLECTIVE_SELF_CONSUMPTION_41 = 0
    COLLECTIVE_SELF_CONSUMPTION_SURPLUS_42 = 1
    NO_SELF_CONSUMPTION = 2
