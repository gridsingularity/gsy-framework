from enum import Enum


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
