from typing import Dict


class PVROI:
    """
    Class that calculates the Return on Investment (ROI), annual cash flow,
    and payback period for a PV asset based on the simulation results.
    """

    def __init__(self):
        pass

    def process_area(self, area):
        print("area", area)
        for area in area["children"]:
            if area["type"] == "PVStrategy":
                print("hey", area)
            elif hasattr(area, "children"):
                self.process_area(area)

    def summary_25_years(self):
        """
        Returns payback period, balance, yearly revenue and profit over a 25-year period.
        """
        summary = {
            "payback_years": 0,
            "final_balance": 0,
            "yearly_revenue": 0,
            "year_to_profit": [{2025: 0}],
        }
        return summary
