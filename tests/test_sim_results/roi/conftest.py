import csv
from pathlib import Path

import pytest

from gsy_framework.sim_results.roi.data_classes import (
    ReplacementTreatment,
    RoiInputs,
    RoiParameterSet,
)

REFERENCE_CASH_FLOW = (
    Path(__file__).parents[2] / "static" / "roi" / "pv_roi_reference_cash_flow.csv"
)

MONEY_PER_YEAR_TOLERANCE = 0.01
MONEY_CUMULATIVE_TOLERANCE = 0.10
YEARS_TOLERANCE = 0.01
IRR_TOLERANCE = 0.0001
LCOE_TOLERANCE = 0.0001


@pytest.fixture(scope="session")
def reference_inputs():
    return RoiInputs(
        capacity_kwp=5,
        capital_cost_per_kwp=1300,
        ownership_share=1,
        avoided_purchase=11.4653723,
        sales_revenue=13.9595022,
        window_generation_kwh=177.1294,
        window_days=7,
        annual_generation_kwh=4900,
        replacement_treatment=ReplacementTreatment.DISCRETE,
    )


@pytest.fixture(scope="session")
def reference_parameters():
    return RoiParameterSet(
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


@pytest.fixture(scope="session")
def reference_cash_flow():
    with open(REFERENCE_CASH_FLOW, newline="", encoding="utf-8") as reference_file:
        rows = list(csv.DictReader(reference_file))
    return {column: [float(row[column]) for row in rows] for column in rows[0]}
