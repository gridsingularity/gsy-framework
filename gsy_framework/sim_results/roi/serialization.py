from typing import Dict

from gsy_framework.sim_results.roi.data_classes import RoiResult

INDICATOR_NAMES = (
    "payback_years",
    "discounted_payback_years",
    "npv",
    "irr",
    "lcoe_per_kwh",
    "lifetime_net_benefit",
)


def serialize_result(result: RoiResult) -> Dict:
    """Return the JSON-safe result in the shape of the backend guide output schema.

    Every indicator with no value has an entry in suppressed that names its cause.
    """
    indicators = {name: getattr(result, name) for name in INDICATOR_NAMES}
    series = result.series
    return {
        **{name: indicator.value for name, indicator in indicators.items()},
        "cash_flow": list(series.cash_flow) if series else [],
        "balance": list(series.balance) if series else [],
        "basis": {
            "annualisation_factor": result.annualisation_factor,
            "seasonally_unadjusted": result.seasonally_unadjusted,
            "parameter_set_version": result.parameter_set_version,
            "replacement_treatment": result.replacement_treatment.value,
        },
        "suppressed": {
            name: indicator.suppressed.value
            for name, indicator in indicators.items()
            if indicator.suppressed is not None
        },
        "unavailable": result.unavailable.value if result.unavailable else None,
    }
