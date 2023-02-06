
from gsy_framework.sim_results.device_statistics import DeviceStatistics
from tests.test_sim_results.test_data import core_stats, area_result_dict, current_market_slot


class TestDeviceStatistics:

    @staticmethod
    def test_device_statistics_are_correctly_calculated():
        device_statistics = DeviceStatistics(True)
        device_statistics.update(area_result_dict, core_stats, current_market_slot)
        expected_results = {
            "House 2": {
                "H2 General Load": {
                    "trade_price_eur": {
                        current_market_slot: [0.1771186441]
                    },
                    "min_trade_price_eur": {
                        current_market_slot: 0.17711864
                    },
                    "max_trade_price_eur": {
                        current_market_slot: 0.17711864
                    },
                    "trade_energy_kWh": {
                        current_market_slot: 0.2
                    },
                    "min_trade_energy_kWh": {
                        current_market_slot: 0.2
                    },
                    "max_trade_energy_kWh": {
                        current_market_slot: 0.2
                    },
                    "load_profile_kWh": {
                        current_market_slot: 0.2
                    },
                    "min_load_profile_kWh": {
                        current_market_slot: 0.2
                    },
                    "max_load_profile_kWh": {
                        current_market_slot: 0.2
                    }
                },
                "H2 PV": {
                    "trade_price_eur": {
                        current_market_slot: [0.1771186441]
                    },
                    "min_trade_price_eur": {
                        current_market_slot: 0.17711864
                    },
                    "max_trade_price_eur": {
                        current_market_slot: 0.17711864
                    },
                    "trade_energy_kWh": {
                        current_market_slot: -0.2
                    },
                    "min_trade_energy_kWh": {
                        current_market_slot: -0.2
                    },
                    "max_trade_energy_kWh": {
                        current_market_slot: -0.2
                    },
                    "pv_production_kWh": {
                        current_market_slot: 0.3108
                    },
                    "min_pv_production_kWh": {
                        current_market_slot: 0.3108
                    },
                    "max_pv_production_kWh": {
                        current_market_slot: 0.3108}
                }
            }
        }

        assert expected_results == device_statistics.device_stats_dict
