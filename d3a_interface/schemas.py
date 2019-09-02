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
    # TODO: Add parameters, once D3ASIM-1378 and D3ASIM-1419 are pushed
    scenario_schema = {
        "definitions": {
            "area": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                    "children": {
                        "type": "array",
                        "items": [
                            {"$ref": "#/definitions/area"},
                            {"$ref": "#/definitions/pv"},
                            {"$ref": "#/definitions/load"},
                            {"$ref": "#/definitions/infinite_power_plant"},
                            {"$ref": "#/definitions/finite_power_plant"},
                            {"$ref": "#/definitions/storage"}
                        ],
                        "default": []}
                },
                "required": ["name"]
            },
            "pv": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                    "panel_count": {"type": "number"},
                    "initial_pv_rate_option": {"type": "number"},
                    "energy_rate_decrease_option": {"type": "number"},
                    "power_profile": {"type": "number"},
                }
            },
            "storage": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                    "battery_capacity": {"type": "number"},
                    "break_even_lower": {"type": "number"},
                    "break_even_upper": {"type": "number"},
                    "initial_capacity": {"type": "number"},
                    "initial_rate_option": {"type": "number"},
                    "max_abs_battery_power": {"type": "number"},
                    "energy_rate_decrease_option": {"type": "number"}
                }
            },
            "load": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                    "hrs_of_day": {"type": "array"},
                    "avg_power_W": {"type": "number"},
                    "hrs_per_day": {"type": "number"},
                    "acceptable_energy_rate": {"type": "number"},
                    "daily_load_profile": {"type": "array"}
                }
            },
            "infinite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                }
            },
            "finite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "number_of_clones": {"type": "number"},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"type": "string"},
                    "energy_rate": {"type": "number"},
                    "max_available_power_kW": {"type": "number"}
                }
            },
        },

        "$ref": "#/definitions/area"
    }


class ResultsSchemas:
    results_schema = {"type": "object",
                      "properties": {
                            "job_id":  {"type": "string"},
                            "random_seed": {"type": "number"},
                            "unmatched_loads": {"type": "object"},
                            "cumulative_loads": {"type": "object"},
                            "price_energy_day": {"type": "object"},
                            "cumulative_grid_trades": {"type": "object"},
                            "bills": {"type": "object"},
                            "tree_summary": {"type": "object"},
                            "status": {"type": "string"},
                            "device_statistics": {"type": "object"},
                            "energy_trade_profile": {"type": "object"}
                          },
                      "additionalProperties": False,
                      "required": ["job_id",
                                   "random_seed",
                                   "unmatched_loads",
                                   "cumulative_loads",
                                   "price_energy_day",
                                   "cumulative_grid_trades",
                                   "bills",
                                   "tree_summary",
                                   "status",
                                   "device_statistics",
                                   "energy_trade_profile"]
                      }
