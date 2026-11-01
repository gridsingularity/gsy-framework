from dataclasses import dataclass
from typing import Dict, List, Optional

from gsy_framework.sim_results.roi.data_classes import (
    AllocationBasis,
    BaselineMethod,
    PriceBasis,
    RoiFlag,
    RoiResult,
    SuppressionCause,
)
from gsy_framework.sim_results.roi.serialization import serialize_result


@dataclass(frozen=True)
class RoiBasis:
    """What a result rests on, so that a reader can tell how far to trust it.

    member_name and member_path are set only on the result of one co-owner.
    """

    baseline_method: BaselineMethod
    allocation_basis: AllocationBasis
    price_basis: PriceBasis
    window_start: Optional[str]
    window_days: float
    window_is_metered: bool
    ownership_share: float
    capacity_kWp: float
    capital_cost_per_kWp: float
    annual_generation_kWh: Optional[float]
    asset_name: str
    owner_name: str
    last_realised_year: Optional[int]
    inputs_observed: List[str]
    inputs_assumed: List[str]
    flags: List[RoiFlag]
    member_name: Optional[str] = None
    member_path: Optional[str] = None

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        basis = {
            "baseline_method": self.baseline_method.value,
            "allocation_basis": self.allocation_basis.value,
            "price_basis": self.price_basis.value,
            "window_start": self.window_start,
            "window_days": self.window_days,
            "window_is_metered": self.window_is_metered,
            "ownership_share": self.ownership_share,
            "capacity_kWp": self.capacity_kWp,
            "capital_cost_per_kWp": self.capital_cost_per_kWp,
            "annual_generation_kWh": self.annual_generation_kWh,
            "asset_name": self.asset_name,
            "owner_name": self.owner_name,
            "last_realised_year": self.last_realised_year,
            "inputs_observed": list(self.inputs_observed),
            "inputs_assumed": list(self.inputs_assumed),
            "flags": sorted(flag.value for flag in self.flags),
        }
        if self.member_name is not None:
            basis.update({"member_name": self.member_name, "member_path": self.member_path})
        return basis


@dataclass(frozen=True)
class PVRoiReport:
    """RoI result of one PV, or of one co-owner of it, as the simulation results report it.

    range holds the low and high cases and is None when the result is unavailable. members is
    keyed by member area name and is None when the PV has no member results.
    """

    result: RoiResult
    basis: RoiBasis
    self_consumption_ratio: Optional[float]
    range: Optional[Dict[str, RoiResult]] = None
    members: Optional[Dict[str, "PVRoiReport"]] = None

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        report = serialize_result(self.result)
        report["basis"].update(self.basis.serializable_dict())
        report["self_consumption_ratio"] = self.self_consumption_ratio
        if self.range is not None:
            report["range"] = {case: serialize_result(roi) for case, roi in self.range.items()}
        if self.members is not None:
            report["members"] = {
                name: member.serializable_dict() for name, member in self.members.items()
            }
        return report


@dataclass(frozen=True)
class FailedPVRoiReport:
    """RoI result of a PV whose appraisal raised, with the error it raised."""

    error: str

    def serializable_dict(self) -> Dict:
        """Return a json serializable representation of the class."""
        return {"unavailable": SuppressionCause.CALCULATION_FAILED.value, "error": self.error}
