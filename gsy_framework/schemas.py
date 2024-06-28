"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

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
from gsy_framework.enums import HeatPumpSourceType


class ScenarioSchemas:
    """JSON schema for validating scenarios."""

    scenario_schema = {
        "definitions": {
            "area": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["Area", "null"]},
                    "name": {"type": "string"},
                    "const_fee_rate": {"type": "number"},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "feed_in_tariff": {"type": ["number", "null"]},
                    "taxes_surcharges": {"type": ["number", "null"]},
                    "coefficient_percentage": {"type": ["number", "null"]},
                    "fixed_monthly_fee": {"type": ["number", "null"]},
                    "marketplace_monthly_fee": {"type": ["number", "null"]},
                    "assistance_monthly_fee": {"type": ["number", "null"]},
                    "market_maker_rate": {"type": ["number", "null"]},
                    "target_market_kpi": {"type": ["number", "null"]},
                    "grid_fee_constant": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "grid_import_fee_const": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "grid_export_fee_const": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "grid_fee_percentage": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "baseline_peak_energy_import_kWh": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "baseline_peak_energy_export_kWh": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "import_capacity_kVA": {"type": ["number", "null"]},
                    "export_capacity_kVA": {"type": ["number", "null"]},
                    "fit_area_boundary": {"type": ["boolean", "null"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "tags": {"anyOf": [{"type": "array"}, {"type": "null"}]},
                    "geo_tag_location": {},
                    "children": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {
                                    "anyOf": [
                                        {"$ref": "#/definitions/area"},
                                        {"$ref": "#/definitions/pv"},
                                        {"$ref": "#/definitions/load"},
                                        {"$ref": "#/definitions/smart_meter"},
                                        {"$ref": "#/definitions/infinite_power_plant"},
                                        {"$ref": "#/definitions/finite_power_plant"},
                                        {"$ref": "#/definitions/storage"},
                                        {"$ref": "#/definitions/scm_storage"},
                                        {"$ref": "#/definitions/wind_turbine"},
                                        {"$ref": "#/definitions/heat_pump"},
                                        {"$ref": "#/definitions/scm_heat_pump"},
                                    ]
                                },
                                "default": [],
                            },
                            {"type": "null"},
                        ]
                    },
                },
                "required": ["name"],
            },
            "pv": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["PV", "PredefinedPV"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "panel_count": {"type": "number"},
                    "initial_selling_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "final_selling_rate": {"type": "number"},
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_decrease_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "capacity_kW": {"type": "number"},
                    "cloud_coverage": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "forecast_stream_id": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "power_profile": {
                        "anyOf": [
                            {"type": "object"},
                            {"type": "number"},
                            {"type": "null"},
                            {"type": "array"},
                            {"type": "string"},
                        ]
                    },
                    "use_market_maker_rate": {"type": "boolean"},
                    "powerProfileUUID": {"type": "string"},
                },
            },
            "wind_turbine": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["WindTurbine"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "initial_selling_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "final_selling_rate": {"type": "number"},
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_decrease_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "power_profile": {
                        "anyOf": [
                            {"type": "object"},
                            {"type": "number"},
                            {"type": "null"},
                            {"type": "array"},
                            {"type": "string"},
                        ]
                    },
                    "use_market_maker_rate": {"type": "boolean"},
                    "powerProfileUUID": {"type": "string"},
                    "capacity_kW": {"type": "number"},
                },
            },
            "storage": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["Storage"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "initial_soc": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "min_allowed_soc": {"type": "number"},
                    "battery_capacity_kWh": {"type": "number"},
                    "max_abs_battery_power_kW": {"type": "number"},
                    "cap_price_strategy": {"type": "boolean"},
                    "initial_selling_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "final_selling_rate": {"type": "number"},
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {"type": "number"},
                    "fit_to_limit": {"type": "boolean"},
                    "energy_rate_increase_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_decrease_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                },
            },
            "load": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["Load"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "avg_power_W": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "initial_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "final_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "fit_to_limit": {"type": ["boolean", "null"]},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "grid_connected": {"type": ["boolean", "null"]},
                    "energy_rate_increase_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "forecast_stream_id": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "daily_load_profile_uuid": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "use_market_maker_rate": {"type": ["boolean", "null"]},
                    "daily_load_profile": {
                        "anyOf": [
                            {"type": "object"},
                            {"type": "array"},
                            {"type": "null"},
                            {"type": "string"},
                        ]
                    },
                },
            },
            "smart_meter": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["SmartMeter"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "initial_selling_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "final_selling_rate": {"type": "number"},
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_decrease_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_increase_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "use_market_maker_rate": {"type": "boolean"},
                },
            },
            "infinite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "enum": ["CommercialProducer", "InfiniteBus", "MarketMaker"]
                    },
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "energy_rate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "energy_buy_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                },
            },
            "finite_power_plant": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["FiniteDieselGenerator", "MarketMaker"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "energy_rate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "max_available_power_kW": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                },
            },
            "heat_pump": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["HeatPump"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "maximum_power_rating_kW": {"type": "number"},
                    "min_temp_C": {"type": "number"},
                    "max_temp_C": {"type": "number"},
                    "initial_temp_C": {"type": "number"},
                    "external_temp_C": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "external_temp_profile_uuid": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "tank_volume_l": {"type": "number"},
                    "consumption_kW": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "consumption_profile_uuid": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "source_type": {
                        "enum": [
                            HeatPumpSourceType.AIR.value,
                            HeatPumpSourceType.GROUND.value,
                        ]
                    },
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "preferred_buying_rate": {"type": "number"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                },
            },
            "scm_heat_pump": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["ScmHeatPump"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "consumption_kW": {
                        "anyOf": [
                            {"type": "object"},
                            {"type": "array"},
                            {"type": "null"},
                            {"type": "string"},
                        ]
                    },
                    "consumption_profile_uuid": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "preferred_buying_rate": {"type": "number"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                },
            },
            "scm_storage": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["ScmStorage"]},
                    "uuid": {"type": "string"},
                    "libraryUUID": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "address": {"type": ["string", "null"]},
                    "allow_external_connection": {"type": ["null", "boolean"]},
                    "geo_tag_location": {},
                    "initial_buying_rate": {"type": "number"},
                    "final_buying_rate": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "fit_to_limit": {"type": "boolean"},
                    "update_interval": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "energy_rate_increase_per_update": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "use_market_maker_rate": {"type": "boolean"},
                    "forecast_stream_id": {
                        "anyOf": [{"type": "number"}, {"type": "null"}]
                    },
                    "prosumption_kWh_profile_uuid": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "prosumption_kWh_profile": {
                        "anyOf": [
                            {"type": "object"},
                            {"type": "array"},
                            {"type": "null"},
                            {"type": "string"},
                        ]
                    },
                },
            },
        },
        "anyOf": [
            {"$ref": "#/definitions/area"},
            {"$ref": "#/definitions/pv"},
            {"$ref": "#/definitions/load"},
            {"$ref": "#/definitions/smart_meter"},
            {"$ref": "#/definitions/infinite_power_plant"},
            {"$ref": "#/definitions/finite_power_plant"},
            {"$ref": "#/definitions/storage"},
            {"$ref": "#/definitions/scm_storage"},
            {"$ref": "#/definitions/wind_turbine"},
            {"$ref": "#/definitions/heat_pump"},
            {"$ref": "#/definitions/scm_heat_pump"},
        ],
        "unevaluatedProperties": False,
    }


class ResultsSchemas:
    """JSON schema for validating results."""

    results_schema = {"type": "object",
                      "properties": {
                          "job_id":  {"type": "string"},
                          "current_market": {"type": "string"},
                          "current_market_ui_time_slot_str": {"type": "string"},
                          "random_seed": {"type": "number"},
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
                          "last_energy_trade_profile": {"type": "object"},
                          "last_device_statistics": {"type": "object"},
                          "last_price_energy_day": {"type": "object"},
                          "kpi": {"type": "object"},
                          "area_throughput": {"type": "object"},
                          "bids_offers_trades": {"type": "object"},
                          "results_area_uuids": {"type": "array"},
                          "simulation_state": {"type": "object"},
                          "cumulative_market_fees": {"type": "number"},
                          "simulation_raw_data": {"type": "object"},
                          "configuration_tree": {"type": "object"}
                      },
                      "additionalProperties": False,
                      "required": ["job_id",
                                   "current_market",
                                   "random_seed",
                                   "status",
                                   "progress_info"]
                      }


class ApiClientConfigSchema:
    """JSON schema for validating data gathered from simulation configuration files."""

    simulation_config_schema = {"type": "object",
                                "username": {"type": "string"},
                                "name": {"type": "string"},
                                "uuid": {"type": "string"},
                                "domain_name": {"type": "string"},
                                "web_socket_domain_name": {"type": "string"},
                                "global_settings": {
                                    "start_date": {"type": "string"},
                                    "spot_market_type": {"type": "string"},
                                    "slot_length": {"type": "string"},
                                    "grid_fee_type": {"type": "string"},
                                    "tick_length": {"type": "string"},
                                    "progress_info":
                                        {"eta_seconds": {"type": "number"},
                                         "elapsed_time_seconds": {"type": "number"},
                                         "percentage_completed": {"type": "number"}},
                                    "slot_length_realtime": {"type": "string"}
                                },
                                "registry": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "uuid": {"type": "string"},
                                    "attributes": {"anyOf": [{"type": "string"},
                                                             {"type": "null"}]},
                                    "registered": {"anyOf": [{"type": "string"},
                                                             {"type": "null"}]},
                                    "aggregator_name": {"anyOf": [{"type": "string"},
                                                                  {"type": "null"}]},
                                    "children": {"anyOf": [{"type": "array"}, {"type": "null"}]}
                                },
                                "required": ["username", "name", "uuid", "domain_name",
                                             "web_socket_domain_name", "global_settings",
                                             "registry"]
                                }


COMMUNITY_DATASHEET_SCHEMA = {
    "type": "object",
    "properties": {
        "settings": {"$ref": "#/$defs/settings"},
        "grid": {"$ref": "#/$defs/grid"},
    },
    "$defs": {
        "settings": {
            "description": "General settings of the community.",
            "type": "object",
            "properties": {
                "start_date": {"type": "custom_pendulum_datetime"},
                "end_date": {"type": "custom_pendulum_datetime"},
                "slot_length": {"type": "custom_timedelta"},
                "currency": {
                    "type": "string",
                    "enum": ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CNY", "CHF"]
                },
                "coefficient_type": {
                    "type": "string",
                    "enum": ["constant", "dynamic"]
                },
                "group_settings": {
                    "type": "string",
                    "enum": ["constant", "dynamic"]
                },
            },
            "required": ["start_date", "end_date", "slot_length", "currency"]
        },
        "grid": {"type": ["object"]}
    }
}
