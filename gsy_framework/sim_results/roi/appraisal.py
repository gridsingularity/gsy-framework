from typing import Optional

from gsy_framework.sim_results.roi.cashflow import annualisation_factor, build_cash_flow_series
from gsy_framework.sim_results.roi.data_classes import (
    Indicator,
    RoiInputs,
    RoiParameterSet,
    RoiResult,
    SuppressionCause,
)
from gsy_framework.sim_results.roi.indicators import (
    internal_rate_of_return,
    levelised_cost,
    payback,
)

MINIMUM_WINDOW_DAYS = 1


def _unavailable_cause(inputs: RoiInputs) -> Optional[SuppressionCause]:
    if inputs.capacity_kwp <= 0 or inputs.window_generation_kwh <= 0:
        return SuppressionCause.NO_GENERATION
    if inputs.window_days < MINIMUM_WINDOW_DAYS:
        return SuppressionCause.WINDOW_TOO_SHORT
    return None


def _unavailable_result(
    inputs: RoiInputs, parameters: RoiParameterSet, cause: SuppressionCause
) -> RoiResult:
    suppressed = Indicator(None, cause)
    return RoiResult(
        parameter_set_version=parameters.version_id,
        replacement_treatment=inputs.replacement_treatment,
        annualisation_factor=None,
        seasonally_unadjusted=False,
        series=None,
        payback_years=suppressed,
        discounted_payback_years=suppressed,
        npv=suppressed,
        irr=suppressed,
        lcoe_per_kwh=suppressed,
        lifetime_net_benefit=suppressed,
        unavailable=cause,
    )


def calculate_roi(inputs: RoiInputs, parameters: RoiParameterSet) -> RoiResult:
    """Appraise one participant from window totals and a published parameter set.

    With zero or negative benefit the series is still returned, since a non-repaying asset is
    a valid result, but payback, discounted payback and IRR are suppressed.
    """
    cause = _unavailable_cause(inputs)
    if cause is not None:
        return _unavailable_result(inputs, parameters, cause)

    annualisation, seasonally_unadjusted = annualisation_factor(
        inputs.window_generation_kwh, inputs.window_days, inputs.annual_generation_kwh
    )
    series = build_cash_flow_series(inputs, parameters, annualisation)

    if inputs.ownership_share * (inputs.avoided_purchase + inputs.sales_revenue) <= 0:
        no_benefit = Indicator(None, SuppressionCause.NON_POSITIVE_BENEFIT)
        payback_years = discounted_payback_years = irr = no_benefit
    else:
        payback_years = payback(series.balance, series.cash_flow)
        discounted_payback_years = payback(series.discounted_balance, series.discounted_cash_flow)
        irr = internal_rate_of_return(series.cash_flow)

    return RoiResult(
        parameter_set_version=parameters.version_id,
        replacement_treatment=inputs.replacement_treatment,
        annualisation_factor=annualisation,
        seasonally_unadjusted=seasonally_unadjusted,
        series=series,
        payback_years=payback_years,
        discounted_payback_years=discounted_payback_years,
        npv=Indicator(sum(series.discounted_cash_flow)),
        irr=irr,
        lcoe_per_kwh=levelised_cost(inputs, series),
        lifetime_net_benefit=Indicator(series.balance[-1]),
    )
