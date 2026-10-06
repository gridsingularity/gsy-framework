from itertools import accumulate
from typing import Optional, Tuple

from gsy_framework.sim_results.roi.data_classes import (
    CashFlowSeries,
    ReplacementTreatment,
    RoiInputs,
    RoiParameterSet,
)

DAYS_PER_YEAR = 365
DAYS_PER_LEAP_YEAR = 366


def annualisation_factor(
    window_generation_kwh: float,
    window_days: float,
    annual_generation_kwh: Optional[float] = None,
) -> Tuple[float, bool]:
    """Return the factor of equation (5) and whether it is seasonally unadjusted.

    A record spanning a full year needs no extrapolation. Without a modelled annual
    generation the factor falls back to the ratio of days, which ignores the season.
    """
    if DAYS_PER_YEAR <= window_days <= DAYS_PER_LEAP_YEAR:
        return 1.0, False
    if window_days > DAYS_PER_LEAP_YEAR:
        return DAYS_PER_YEAR / window_days, False
    if annual_generation_kwh is not None and annual_generation_kwh > 0:
        return annual_generation_kwh / window_generation_kwh, False
    return DAYS_PER_YEAR / window_days, True


def asset_replacement_cost(
    year: int,
    treatment: ReplacementTreatment,
    capacity_kwp: float,
    parameters: RoiParameterSet,
) -> float:
    """Return the replacement cost of the whole asset in a year from 1 to the horizon.

    The discrete treatment is equation (8). The reserve treatment spreads the same total
    evenly over years 1 to the replacement year.
    """
    total = parameters.replacement_cost_per_kwp * capacity_kwp
    if treatment is ReplacementTreatment.RESERVE:
        return total / parameters.replacement_year if year <= parameters.replacement_year else 0.0
    return total if year == parameters.replacement_year else 0.0


def build_cash_flow_series(
    inputs: RoiInputs, parameters: RoiParameterSet, annualisation: float
) -> CashFlowSeries:
    """Build the yearly series of equations (6) to (10) and (16)."""
    share = inputs.ownership_share
    benefit_share = 1.0 if inputs.benefit_is_apportioned else share
    avoided_first_year = annualisation * benefit_share * inputs.avoided_purchase
    sales_first_year = annualisation * benefit_share * inputs.sales_revenue
    operating_first_year = parameters.operating_cost_per_kwp * inputs.capacity_kwp

    cash_flow = [-share * inputs.capital_cost_per_kwp * inputs.capacity_kwp]
    asset_operating_cost = [0.0]
    replacement_costs = [0.0]
    generation_kwh = [0.0]
    for year in range(1, parameters.horizon_years + 1):
        degradation = (1 - parameters.degradation_rate) ** year
        retail_escalation = (1 + parameters.retail_escalation_rate) ** year
        export_escalation = (1 + parameters.export_escalation_rate) ** year
        operating = operating_first_year * retail_escalation
        replacement = asset_replacement_cost(
            year, inputs.replacement_treatment, inputs.capacity_kwp, parameters
        )
        benefit = (
            avoided_first_year * degradation * retail_escalation
            + sales_first_year * degradation * export_escalation
        )
        cash_flow.append(benefit - share * (operating + replacement))
        asset_operating_cost.append(operating)
        replacement_costs.append(replacement)
        generation_kwh.append(annualisation * inputs.window_generation_kwh * degradation)

    discount_factor = [
        1 / (1 + parameters.discount_rate) ** year for year in range(len(cash_flow))
    ]
    discounted_cash_flow = [flow * factor for flow, factor in zip(cash_flow, discount_factor)]
    return CashFlowSeries(
        cash_flow=tuple(cash_flow),
        balance=tuple(accumulate(cash_flow)),
        discounted_cash_flow=tuple(discounted_cash_flow),
        discounted_balance=tuple(accumulate(discounted_cash_flow)),
        asset_operating_cost=tuple(asset_operating_cost),
        asset_replacement_cost=tuple(replacement_costs),
        generation_kwh=tuple(generation_kwh),
        discount_factor=tuple(discount_factor),
    )
