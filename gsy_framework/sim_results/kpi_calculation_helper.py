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
    ) -> Optional[float]:
        """Savings ranking of an area compared to other areas. Value range: [0.0, 1.0]"""
        if (max_community_savings_percent -
                min_community_savings_percent) <= FLOATING_POINT_TOLERANCE:
            return None
        return ((savings_percent - min_community_savings_percent) /
                (max_community_savings_percent - min_community_savings_percent))

    @classmethod
    def saving_absolute(
            cls, total_base_energy_cost_excl_revenue: float,
            total_gsy_e_cost_excl_revenue: float
    ) -> float:
        """Calculate the difference between the bill using the P2P trading and the bill
        that would use the current allowed energy trading; basically paying the market maker rate
        for energy if taken from the grid and receiving the feed-in-tariff when sending available
        energy to the grid."""
        return total_base_energy_cost_excl_revenue - total_gsy_e_cost_excl_revenue

    @classmethod
    def saving_percentage(
            cls, saving_absolute: float, total_base_energy_cost_excl_revenue: float) -> float:
        """Calculate the percentage of saving."""
        return (abs((saving_absolute / total_base_energy_cost_excl_revenue) * 100)
                if total_base_energy_cost_excl_revenue > FLOATING_POINT_TOLERANCE else 0)
