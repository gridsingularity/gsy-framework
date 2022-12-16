from typing import Optional

from gsy_framework.constants_limits import FLOATING_POINT_TOLERANCE


class KPICalculationHelper:
    """Encapsulates all KPI-related calculations in a class, for readability purposes."""

    @classmethod
    def self_sufficiency(
            cls, total_self_consumption_wh: float, total_energy_demanded_wh: float
    ) -> Optional[float]:
        """Self-sufficiency is the ability of an area to provide its energy
        needs from its own resources. Value range: [0.0, 1.0]"""
        if total_energy_demanded_wh <= FLOATING_POINT_TOLERANCE:
            return None
        if total_self_consumption_wh >= total_energy_demanded_wh:
            return 1.0
        return total_self_consumption_wh / total_energy_demanded_wh

    @classmethod
    def self_consumption(
            cls, total_self_consumption_wh: float, total_energy_produced_wh: float
    ) -> Optional[float]:
        """Self-consumption indicates the portion of the energy used by an area from the total
        amount of energy produced by it. Value range: [0.0, 1.0]"""
        if total_energy_produced_wh <= FLOATING_POINT_TOLERANCE:
            return None
        if total_self_consumption_wh >= total_energy_produced_wh:
            return 1.0
        return total_self_consumption_wh / total_energy_produced_wh

    @classmethod
    def energy_benchmark(
            cls, savings_percent: float,
            min_community_savings_percent: float,
            max_community_savings_percent: float
    ) -> float:
        """Savings ranking of an area compared to other areas. Value range: [0.0, 1.0]"""
        if (max_community_savings_percent -
                min_community_savings_percent) <= FLOATING_POINT_TOLERANCE:
            return 0.0
        return ((savings_percent - min_community_savings_percent) /
                (max_community_savings_percent - min_community_savings_percent))
