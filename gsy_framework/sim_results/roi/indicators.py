from typing import Optional, Sequence

from gsy_framework.sim_results.roi.data_classes import (
    CashFlowSeries,
    Indicator,
    RoiInputs,
    SuppressionCause,
)

IRR_BISECTION_STEPS = 200


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def sign_changes(cash_flow: Sequence[float]) -> int:
    """Count sign changes between consecutive non-zero values, as Descartes rule requires."""
    signs = [_sign(value) for value in cash_flow if value != 0]
    return sum(1 for previous, current in zip(signs, signs[1:]) if previous != current)


def interpolated_crossing(balance: Sequence[float], cash_flow: Sequence[float]) -> Optional[float]:
    """Return the year the balance first turns non-negative, interpolated as in equation (11).

    Only the first crossing counts. A balance that falls back below zero later, for example
    in the replacement year, does not move it.
    """
    for year in range(1, len(balance)):
        if balance[year] >= 0:
            return (year - 1) + abs(balance[year - 1]) / cash_flow[year]
    return None


def payback(balance: Sequence[float], cash_flow: Sequence[float]) -> Indicator:
    """Return a payback indicator, suppressed when the balance never breaks even."""
    crossing = interpolated_crossing(balance, cash_flow)
    if crossing is None:
        return Indicator(None, SuppressionCause.NEVER_BREAKS_EVEN)
    return Indicator(crossing)


def internal_rate_of_return(cash_flow: Sequence[float]) -> Indicator:
    """Return the root of equation (14), or suppress it when the root is not unique.

    The root is found in x = 1 / (1 + IRR), where the net present value is a polynomial with
    exactly one positive root whenever the signs change exactly once.
    """
    if sign_changes(cash_flow) != 1:
        return Indicator(None, SuppressionCause.IRR_NOT_UNIQUE)

    def present_value(x: float) -> float:
        return sum(flow * x**year for year, flow in enumerate(cash_flow))

    sign_near_zero = next(_sign(flow) for flow in cash_flow if flow != 0)
    low, high = 0.0, 1.0
    while _sign(present_value(high)) == sign_near_zero:
        high *= 2
    for _ in range(IRR_BISECTION_STEPS):
        middle = (low + high) / 2
        if _sign(present_value(middle)) == sign_near_zero:
            low = middle
        else:
            high = middle
    return Indicator(1 / ((low + high) / 2) - 1)


def levelised_cost(inputs: RoiInputs, series: CashFlowSeries) -> Indicator:
    """Return the asset-level cost per kWh of equations (15) and (16)."""
    discounted_generation = sum(
        energy * factor for energy, factor in zip(series.generation_kwh, series.discount_factor)
    )
    discounted_cost = sum(
        (operating + replacement) * factor
        for operating, replacement, factor in zip(
            series.asset_operating_cost, series.asset_replacement_cost, series.discount_factor
        )
    )
    capital_cost = inputs.capital_cost_per_kwp * inputs.capacity_kwp
    return Indicator((capital_cost + discounted_cost) / discounted_generation)
