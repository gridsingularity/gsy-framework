from pathlib import Path

import openpyxl
import pytest

from gsy_framework.sim_results.roi.data_classes import (
    ReplacementTreatment,
    RoiInputs,
    RoiParameterSet,
)

REFERENCE_WORKBOOK = Path(__file__).parents[2] / "static" / "roi" / "PV_RoI_Reference_Model.xlsx"

MONEY_PER_YEAR_TOLERANCE = 0.01
MONEY_CUMULATIVE_TOLERANCE = 0.10
YEARS_TOLERANCE = 0.01
LCOE_TOLERANCE = 0.0001
FIRST_YEAR_ROW = 4
LAST_YEAR_ROW = 29


@pytest.fixture(scope="session")
def workbook():
    return openpyxl.load_workbook(REFERENCE_WORKBOOK, data_only=True)


@pytest.fixture(scope="session")
def reference_inputs(workbook):
    sheet = workbook["Inputs"]
    return RoiInputs(
        capacity_kwp=sheet["B6"].value,
        capital_cost_per_kwp=sheet["B7"].value,
        ownership_share=sheet["B9"].value,
        avoided_purchase=sheet["B46"].value,
        sales_revenue=sheet["B47"].value,
        window_generation_kwh=sheet["B37"].value,
        window_days=sheet["B35"].value,
        annual_generation_kwh=sheet["B36"].value,
        replacement_treatment=ReplacementTreatment(sheet["B42"].value),
    )


@pytest.fixture(scope="session")
def reference_parameters(workbook):
    sheet = workbook["Inputs"]
    return RoiParameterSet(
        version_id=sheet["B13"].value,
        horizon_years=sheet["B14"].value,
        degradation_rate=sheet["B15"].value,
        operating_cost_per_kwp=sheet["B16"].value,
        retail_escalation_rate=sheet["B17"].value,
        export_escalation_rate=sheet["B18"].value,
        discount_rate=sheet["B19"].value,
        replacement_year=sheet["B20"].value,
        replacement_cost_per_kwp=sheet["B21"].value,
    )


def cash_flow_column(workbook, column: str):
    sheet = workbook["CashFlow"]
    return [sheet[f"{column}{row}"].value for row in range(FIRST_YEAR_ROW, LAST_YEAR_ROW + 1)]
