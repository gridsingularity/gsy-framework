from dataclasses import replace
from typing import Dict, Tuple

from gsy_framework.sim_results.roi.appraisal import calculate_roi
from gsy_framework.sim_results.roi.data_classes import (
    RangeLevers,
    RoiInputs,
    RoiParameterSet,
    RoiResult,
)

CASES = {"low": 0, "high": 1}


def calculate_range(
    inputs: RoiInputs,
    parameters: RoiParameterSet,
    levers: RangeLevers,
    own_consumption_kWh: float,
    sold_kWh: float,
) -> Dict[str, RoiResult]:
    """Return the low and high cases of the reported range.

    Scaling self-consumption moves energy between own use and sales, each valued at its average
    rate over the window. The high case can move at most the energy that was actually sold.
    """
    return {
        case: calculate_roi(
            *_case_inputs(inputs, parameters, levers, own_consumption_kWh, sold_kWh, index)
        )
        for case, index in CASES.items()
    }


def _case_inputs(
    inputs: RoiInputs,
    parameters: RoiParameterSet,
    levers: RangeLevers,
    own_consumption_kWh: float,
    sold_kWh: float,
    index: int,
) -> Tuple[RoiInputs, RoiParameterSet]:
    shifted_kWh = own_consumption_kWh * (levers.self_consumption_multiplier[index] - 1)
    shifted_kWh = min(shifted_kWh, sold_kWh)
    avoided_rate = inputs.avoided_purchase / own_consumption_kWh if own_consumption_kWh else 0.0
    sale_rate = inputs.sales_revenue / sold_kWh if sold_kWh else 0.0
    case_inputs = replace(
        inputs,
        avoided_purchase=inputs.avoided_purchase + shifted_kWh * avoided_rate,
        sales_revenue=inputs.sales_revenue - shifted_kWh * sale_rate,
        capital_cost_per_kWp=inputs.capital_cost_per_kWp * levers.capital_cost_factor[index],
    )
    case_parameters = replace(
        parameters,
        retail_escalation_rate=levers.retail_escalation_rate[index],
        degradation_rate=levers.degradation_rate[index],
    )
    return case_inputs, case_parameters
