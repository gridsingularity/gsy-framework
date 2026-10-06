from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class ReplacementTreatment(Enum):
    """How the inverter replacement cost enters the cash flow."""

    DISCRETE = "discrete"
    RESERVE = "reserve"


class SuppressionCause(Enum):
    """Why an indicator or a whole result carries no value."""

    NEVER_BREAKS_EVEN = "never_breaks_even"
    IRR_NOT_UNIQUE = "irr_not_unique"
    NON_POSITIVE_BENEFIT = "non_positive_benefit"
    NO_GENERATION = "no_generation"
    WINDOW_TOO_SHORT = "window_too_short"


@dataclass(frozen=True)
class RoiParameterSet:
    """Assumed appraisal parameters, published under a version id and never edited after.

    Rates are fractions per year. Costs are in currency per kWp, and currency per kWp per year
    for operating cost.
    """

    version_id: str
    horizon_years: int
    degradation_rate: float
    operating_cost_per_kwp: float
    retail_escalation_rate: float
    export_escalation_rate: float
    discount_rate: float
    replacement_year: int
    replacement_cost_per_kwp: float

    def __post_init__(self):
        if not 0 <= self.degradation_rate < 1:
            raise ValueError(f"Degradation rate must be in [0, 1), got {self.degradation_rate}.")
        if self.discount_rate <= -1:
            raise ValueError(f"Discount rate must exceed -1, got {self.discount_rate}.")
        if not 1 <= self.replacement_year <= self.horizon_years:
            raise ValueError(
                f"Replacement year must lie within the horizon, got {self.replacement_year}."
            )


@dataclass(frozen=True)
class RoiInputs:
    """Observed and user-supplied quantities for one participant over one assessment window.

    The avoided purchase and sales revenue are the window totals of equations (4a) and (4b).
    Without an annual generation figure, annualisation falls back to the ratio of days.
    """

    capacity_kwp: float
    capital_cost_per_kwp: float
    ownership_share: float
    avoided_purchase: float
    sales_revenue: float
    window_generation_kwh: float
    window_days: float
    annual_generation_kwh: Optional[float] = None
    replacement_treatment: ReplacementTreatment = ReplacementTreatment.DISCRETE


@dataclass(frozen=True)
class Indicator:
    """A computed value, or None together with the cause that suppressed it."""

    value: Optional[float]
    suppressed: Optional[SuppressionCause] = None


@dataclass(frozen=True)
class CashFlowSeries:
    """Yearly series indexed by year, from 0 to the horizon.

    Cash flows and balances are apportioned by ownership share. Operating cost, replacement
    cost and generation are for the whole asset, since the levelised cost is asset-level.
    """

    cash_flow: Tuple[float, ...]
    balance: Tuple[float, ...]
    discounted_cash_flow: Tuple[float, ...]
    discounted_balance: Tuple[float, ...]
    asset_operating_cost: Tuple[float, ...]
    asset_replacement_cost: Tuple[float, ...]
    generation_kwh: Tuple[float, ...]
    discount_factor: Tuple[float, ...]


@dataclass(frozen=True)
class RoiResult:
    """Appraisal of one participant.

    When unavailable is set, series is None and every indicator carries that cause.
    """

    parameter_set_version: str
    replacement_treatment: ReplacementTreatment
    annualisation_factor: Optional[float]
    seasonally_unadjusted: bool
    series: Optional[CashFlowSeries]
    payback_years: Indicator
    discounted_payback_years: Indicator
    npv: Indicator
    irr: Indicator
    lcoe_per_kwh: Indicator
    lifetime_net_benefit: Indicator
    unavailable: Optional[SuppressionCause] = None
