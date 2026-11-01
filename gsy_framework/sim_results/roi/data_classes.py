from dataclasses import asdict, dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Dict, List, Optional, Tuple

from gsy_framework.enums import RandomOrder


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
    CALCULATION_FAILED = "calculation_failed"


class RoiFlag(Enum):
    """Why a result is less certain than its inputs suggest."""

    STORAGE_CAPEX_EXCLUDED = "storage_capex_excluded"
    NOT_SEPARABLE = "not_separable"
    PERCENTAGE_GRID_FEES_EXCLUDED = "percentage_grid_fees_excluded"
    SHARED_ASSET_ESTIMATE = "shared_asset_estimate"
    MEMBER_RESULTS_WITHHELD = "member_results_withheld"


class BaselineMethod(Enum):
    """What the bill without the asset is taken from."""

    ANALYTICAL = "analytical"
    SIMULATION = "simulation"


class PriceBasis(Enum):
    """Whether the supplier rate varied over the window or stayed at one value."""

    PROFILE = "profile"
    SCALAR = "scalar"


class AllocationBasis(Enum):
    """How the energy of the asset is split between own use and sales."""

    MARKET_CLEARING = "market_clearing"


@dataclass(frozen=True)
class RoiParameterSet:
    """Assumed appraisal parameters, published under a version id and never edited after.

    Rates are fractions per year. Costs are in currency per kWp, and currency per kWp per year
    for operating cost.
    """

    version_id: str
    horizon_years: int
    degradation_rate: float
    operating_cost_per_kWp: float
    retail_escalation_rate: float
    export_escalation_rate: float
    discount_rate: float
    replacement_year: int
    replacement_cost_per_kWp: float

    def __post_init__(self):
        if not 0 <= self.degradation_rate < 1:
            raise ValueError(f"Degradation rate must be in [0, 1), got {self.degradation_rate}.")
        for name in ("discount_rate", "retail_escalation_rate", "export_escalation_rate"):
            if getattr(self, name) <= -1:
                raise ValueError(f"{name} must exceed -1, got {getattr(self, name)}.")
        if not 1 <= self.replacement_year <= self.horizon_years:
            raise ValueError(
                f"Replacement year must lie within the horizon, got {self.replacement_year}."
            )


@dataclass(frozen=True)
class RangeLevers:
    """Low and high values of the four levers D7.3 names for the reported range.

    Each pair is (low case, high case), so the low case is the pessimistic one.
    """

    self_consumption_multiplier: Tuple[float, float]
    retail_escalation_rate: Tuple[float, float]
    capital_cost_factor: Tuple[float, float]
    degradation_rate: Tuple[float, float]


@dataclass(frozen=True)
class RoiInputs:
    """Observed and user-supplied quantities for one participant over one assessment window.

    The avoided purchase and sales revenue are the window totals of equations (4a) and (4b).
    Without an annual generation figure, annualisation falls back to the ratio of days.

    A member of a shared installation who reports their own bill difference has already taken
    their part of the benefit, so benefit_is_apportioned stops equation (6) applying the share
    to it again, as the Shared sheet of the reference model does. The share still apportions the
    capital and operating cost.
    """

    capacity_kWp: float
    capital_cost_per_kWp: float
    ownership_share: float
    avoided_purchase: float
    sales_revenue: float
    window_generation_kWh: float
    window_days: float
    annual_generation_kWh: Optional[float] = None
    replacement_treatment: ReplacementTreatment = ReplacementTreatment.DISCRETE
    benefit_is_apportioned: bool = False

    def __post_init__(self):
        quantities = (
            self.capacity_kWp,
            self.capital_cost_per_kWp,
            self.ownership_share,
            self.avoided_purchase,
            self.sales_revenue,
            self.window_generation_kWh,
            self.window_days,
            0.0 if self.annual_generation_kWh is None else self.annual_generation_kWh,
        )
        if not all(isfinite(quantity) for quantity in quantities):
            raise ValueError(f"Every quantity must be finite, got {quantities}.")
        if self.capital_cost_per_kWp <= 0:
            raise ValueError(f"Capital cost must be positive, got {self.capital_cost_per_kWp}.")
        if not 0 <= self.ownership_share <= 1:
            raise ValueError(f"Ownership share must be in [0, 1], got {self.ownership_share}.")


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
    generation_kWh: Tuple[float, ...]
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
    lcoe_per_kWh: Indicator
    lifetime_net_benefit: Indicator
    unavailable: Optional[SuppressionCause] = None


@dataclass(frozen=True)
class PVRoiParameters:
    """Inputs of a PV that only the RoI results use.

    annual_generation_kWh is the modelled generation over a full year, which lets a short run be
    annualised by season rather than by days. ownership_shares holds the share of each co-owning
    member area, keyed by its name.
    """

    capital_cost_per_kWp: Optional[float] = None
    annual_generation_kWh: Optional[float] = None
    ownership_shares: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, parameters: Dict) -> "PVRoiParameters":
        """Build the parameters from their serializable dict, in which every key is optional.

        Raises a TypeError for a key that is not a parameter.
        """
        return cls(**{**parameters, "ownership_shares": parameters.get("ownership_shares") or {}})

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return asdict(self)


@dataclass(frozen=True)
class AreaFingerprint:
    """Settings of one area that must match for its bill to be comparable across two runs.

    settings is a sha256 of the remaining settings of the area, or None when it has none.
    """

    type: str
    grid_fee_constant: Optional[float]
    grid_fee_percentage: Optional[float]
    settings: Optional[str]


@dataclass(frozen=True)
class SimulationFingerprint:
    """Settings that two runs must share for their bills to be comparable.

    areas is keyed by the path of area names from the root, as in "Community/House 1".
    """

    seed: Optional[int]
    start_date: str
    sim_duration_seconds: float
    slot_length_seconds: float
    tick_length_seconds: float
    market_type: int
    bid_offer_match_type: int
    grid_fee_type: int
    random_order: RandomOrder
    areas: Dict[str, AreaFingerprint]


@dataclass(frozen=True)
class RoiBaseline:
    """Bills from a run without the asset, which a run with the asset compares its bills to.

    area_bills is keyed by area name path and supplier_rates by time slot.
    """

    fingerprint: SimulationFingerprint
    area_bills: Dict[str, float]
    supplier_rates: Dict[str, float]

    @classmethod
    def from_dict(cls, baseline: Dict) -> "RoiBaseline":
        """Build a baseline from its serializable dict.

        Raises a ValueError naming every missing or wrongly typed key by its path.
        """
        reader = _BaselineReader()
        result = reader.baseline(baseline)
        if reader.errors:
            raise ValueError("Invalid RoI baseline: " + ", ".join(reader.errors) + ".")
        return result

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        fingerprint = asdict(self.fingerprint)
        fingerprint["random_order"] = self.fingerprint.random_order.value
        return {
            "fingerprint": fingerprint,
            "area_bills": dict(self.area_bills),
            "supplier_rates": dict(self.supplier_rates),
        }


_NUMBER = (int, float)
_NONE = type(None)


class _BaselineReader:
    """Reads a baseline dict and collects every error, so one ValueError names them all."""

    def __init__(self):
        self.errors: List[str] = []

    def baseline(self, source: Any) -> Optional[RoiBaseline]:
        if not self._is_dict(source, "baseline"):
            return None
        fingerprint = self._fingerprint(self.read(source, "", "fingerprint", (dict,)))
        area_bills = self._rates(source, "area_bills")
        supplier_rates = self._rates(source, "supplier_rates")
        if self.errors:
            return None
        return RoiBaseline(fingerprint, area_bills, supplier_rates)

    def read(self, source: Dict, path: str, key: str, kinds: Tuple[type, ...]) -> Any:
        """Return source[key], or None after recording why it is missing or of the wrong type."""
        name = f"{path}.{key}" if path else key
        if key not in source:
            self.errors.append(f"{name} is missing")
            return None
        value = source[key]
        if isinstance(value, bool) or not isinstance(value, kinds):
            expected = " or ".join("None" if kind is _NONE else kind.__name__ for kind in kinds)
            self.errors.append(f"{name} must be {expected}, got {type(value).__name__}")
            return None
        return float(value) if float in kinds and value is not None else value

    def _is_dict(self, value: Any, name: str) -> bool:
        if isinstance(value, dict):
            return True
        self.errors.append(f"{name} must be dict, got {type(value).__name__}")
        return False

    def _fingerprint(self, source: Optional[Dict]) -> Optional[SimulationFingerprint]:
        if source is None:
            return None
        path = "fingerprint"
        seed = self.read(source, path, "seed", (int, _NONE))
        start_date = self.read(source, path, "start_date", (str,))
        durations = [
            self.read(source, path, key, _NUMBER)
            for key in ("sim_duration_seconds", "slot_length_seconds", "tick_length_seconds")
        ]
        types = [
            self.read(source, path, key, (int,))
            for key in ("market_type", "bid_offer_match_type", "grid_fee_type")
        ]
        random_order = self._random_order(self.read(source, path, "random_order", (str,)))
        areas = self._areas(self.read(source, path, "areas", (dict,)))
        if self.errors:
            return None
        return SimulationFingerprint(seed, start_date, *durations, *types, random_order, areas)

    def _random_order(self, value: Optional[str]) -> Optional[RandomOrder]:
        if value is None:
            return None
        try:
            return RandomOrder(value)
        except ValueError:
            allowed = ", ".join(order.value for order in RandomOrder)
            self.errors.append(f"fingerprint.random_order must be one of {allowed}, got {value!r}")
            return None

    def _areas(self, source: Optional[Dict]) -> Dict[str, AreaFingerprint]:
        areas = {}
        for name, area in (source or {}).items():
            path = f"fingerprint.areas.{name}"
            if not self._is_dict(area, path):
                continue
            areas[name] = AreaFingerprint(
                type=self.read(area, path, "type", (str,)),
                grid_fee_constant=self.read(area, path, "grid_fee_constant", (*_NUMBER, _NONE)),
                grid_fee_percentage=self.read(
                    area, path, "grid_fee_percentage", (*_NUMBER, _NONE)
                ),
                settings=self.read(area, path, "settings", (str, _NONE)),
            )
        return areas

    def _rates(self, source: Dict, key: str) -> Dict[str, float]:
        rates = {}
        for name, rate in (self.read(source, "", key, (dict,)) or {}).items():
            if isinstance(rate, bool) or not isinstance(rate, _NUMBER):
                self.errors.append(f"{key}.{name} must be float, got {type(rate).__name__}")
                continue
            rates[name] = float(rate)
        return rates
