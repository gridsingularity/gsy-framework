from gsy_framework.sim_results.roi.data_classes import RoiParameterSet

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
