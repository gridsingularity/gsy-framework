"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class ScenarioSchemas:
    scenario_schema = {
        "definitions": {
            "area": {
                "type": "object",
                "properties": {
                    "type": {"anyOf": [{"enum": ["Area"]}, {"enum": ["null"]}]},
                    "name": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "grid_fee_percentage": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "baseline_peak_energy_import_kWh":
                        {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "baseline_peak_energy_export_kWh":
                        {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "children": {"anyOf": [{
                                    "type": "array",
                                    "items": {"anyOf": [
                                        {"$ref": "#/definitions/area"},
                                        {"$ref": "#/definitions/pv"},
                                        {"$ref": "#/definitions/load"},
                                        {"$ref": "#/definitions/infinite_power_plant"},
                                        {"$ref": "#/definitions/finite_power_plant"},
                                        {"$ref": "#/definitions/storage"}
                                    ]}, "default": []},
                                    {"type": "null"}]}
                },
                "required": ["name"]
            },
            "pv": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["PV", "PredefinedPV"]},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "panel_count": {"type": "number"},
                    "initial_selling_rate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "final_selling_rate": {"type": "number"},
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "energy_rate_decrease_per_update": {"anyOf": [{"type": "number"},
                                                                  {"type": "null"}]},
                    "max_panel_power_W": {"type": "number"},
                    "cloud_coverage": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "power_profile": {"anyOf": [{"type": "number"},
                                                {"type": "null"},
                                                {"type": "array"},
                                                {"type": "string"}]},
                    "use_market_maker_rate": {"type": "boolean"}
                }
            },
            "storage": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["Storage"]},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "initial_soc": {"type": "number"},
                    "min_allowed_soc": {"type": "number"},
                    "battery_capacity_kWh": {"type": "number"},
                    "max_abs_battery_power_kW": {"type": "number"},
                    "cap_price_strategy": {"type": "boolean"},
                    "initial_selling_rate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "final_selling_rate": {"type": "number"},
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {"type": "number"},
                    "fit_to_limit": {"type": "boolean"},
                    "energy_rate_increase_per_update":  {"anyOf": [{"type": "number"},
                                                                   {"type": "null"}]},
                    "energy_rate_decrease_per_update":  {"anyOf": [{"type": "number"},
                                                                   {"type": "null"}]},
                    "update_interval":  {"anyOf": [{"type": "number"}, {"type": "null"}]}
                }
            },
            "load": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["Load"]},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "avg_power_W":  {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "hrs_per_day":  {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "hrs_of_day": {"anyOf": [{"type": "array"}, {"type": "null"}]},
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval":  {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "energy_rate_increase_per_update": {"anyOf": [{"type": "number"},
                                                                  {"type": "null"}]},
                    "daily_load_profile_uuid": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "use_market_maker_rate": {"type": "boolean"},
                    "daily_load_profile": {"anyOf": [{"type": "array"},
                                                     {"type": "null"},
                                                     {"type": "string"}]}
                }
            },
            "infinite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["CommercialProducer", "InfiniteBus", "MarketMaker"]},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                }
            },
            "finite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["FiniteDieselGenerator", "MarketMaker"]},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "energy_rate":  {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "max_available_power_kW":  {"anyOf": [{"type": "number"}, {"type": "null"}]}
                }
            },
        },

        "anyOf": [
            {"$ref": "#/definitions/area"},
            {"$ref": "#/definitions/pv"},
            {"$ref": "#/definitions/load"},
            {"$ref": "#/definitions/infinite_power_plant"},
            {"$ref": "#/definitions/finite_power_plant"},
            {"$ref": "#/definitions/storage"}
        ]
    }


class ResultsSchemas:
    results_schema = {"type": "object",
                      "properties": {
                            "job_id":  {"type": "string"},
                            "current_market": {"type": "string"},
                            "random_seed": {"type": "number"},
                            "unmatched_loads": {"type": "object"},
                            "price_energy_day": {"type": "object"},
                            "cumulative_grid_trades": {"type": "object"},
                            "bills": {"type": "object"},
                            "cumulative_bills": {"type": "object"},
                            "status": {"type": "string"},
                            "progress_info": {
                                "eta_seconds": {"type": "number"},
                                "elapsed_time_seconds": {"type": "number"},
                                "percentage_completed": {"type": "number"},
                            },
                            "device_statistics": {"type": "object"},
                            "energy_trade_profile": {"type": "object"},
                            "last_unmatched_loads": {"type": "object"},
                            "last_energy_trade_profile": {"type": "object"},
                            "last_device_statistics": {"type": "object"},
                            "last_price_energy_day": {"type": "object"},
                            "kpi": {"type": "object"},
                            "area_throughput": {"type": "object"},
                            "last_energy_trades_high_resolution": {"type": "object"},
                            "bids_offers_trades": {"type": "object"},
                            "results_area_uuids": {"type": "array"},
                            "simulation_state": {"type": "object"},
                            "cumulative_market_fees": {"type": "number"},
                          },
                      "additionalProperties": False,
                      "required": ["job_id",
                                   "random_seed",
                                   "cumulative_grid_trades",
                                   "bills",
                                   "cumulative_bills",
                                   "status",
                                   "progress_info"]
                      }
