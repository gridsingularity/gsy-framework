from enum import Enum

from pendulum import duration


class BidOfferMatchAlgoEnum(Enum):
    """Matching algorithms supported by the GSY exchange."""
    PAY_AS_BID = 1
    PAY_AS_CLEAR = 2
    EXTERNAL = 3
    DOF = 4


class SpotMarketTypeEnum(Enum):
    """Types of markets supported by the GSY exchange."""

    ONE_SIDED = 1
    TWO_SIDED = 2
    COEFFICIENTS = 3


class CoefficientAlgorithm(Enum):
    """Coefficient algorithms supported by the GSY exchange."""

    STATIC = 1
    DYNAMIC = 2


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

    def __str__(self):
        return {
            self.SPOT: "SPOT",
            self.BALANCING: "BALANCING",
            self.SETTLEMENT: "SETTLEMENT",
            self.FUTURE: "FUTURE",
            self.DAY_FORWARD: "DAY_FORWARD",
            self.WEEK_FORWARD: "WEEK_FORWARD",
            self.MONTH_FORWARD: "MONTH_FORWARD",
            self.YEAR_FORWARD: "YEAR_FORWARD",
            self.INTRADAY: "INTRADAY"
        }[self]


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
            self.RES_1_YEAR: duration(years=1)
        }[self]
