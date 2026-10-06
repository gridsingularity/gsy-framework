from gsy_framework.sim_results.roi.data_classes import RangeLevers, RoiParameterSet

EU_2026_1 = RoiParameterSet(
    version_id="EU-2026.1",
    horizon_years=25,
    degradation_rate=0.005,
    operating_cost_per_kwp=13,
    retail_escalation_rate=0.02,
    export_escalation_rate=0.01,
    discount_rate=0.04,
    replacement_year=13,
    replacement_cost_per_kwp=180,
)

DEFAULT_PARAMETER_SET = EU_2026_1

# D7.3 Table 1 elicits capital cost per jurisdiction rather than in the parameter set. This is
# the EU-2026.1 default the reference model uses when the user gives none.
DEFAULT_CAPITAL_COST_PER_KWP = 1300

# Self-consumption, retail escalation and capital cost are the Sensitivity levers of the reference
# model (Inputs!B53:D55), with capital cost expressed relative to 1300 EUR/kWp. Degradation spans
# the 0.4%/year premium warranty and the 1.0%/year recent median in D7.3 Table 1.
EU_2026_1_RANGE = RangeLevers(
    self_consumption_multiplier=(0.75, 1.25),
    retail_escalation_rate=(0.005, 0.035),
    capital_cost_factor=(1550 / 1300, 1100 / 1300),
    degradation_rate=(0.01, 0.004),
)

DEFAULT_RANGE_LEVERS = EU_2026_1_RANGE
