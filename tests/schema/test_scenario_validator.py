from gsy_framework.schema.validators import get_schema_validator


class TestScenarioValidator:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        self._data = {
          "name": "Grid",
          "tags": None,
          "uuid": "bd867ebb-f3c8-4d8d-926a-a4181fa86c3a",
          "children": [
            {
              "name": "Grid Market",
              "type": "InfiniteBus",
              "uuid": "227ecfdf-0e60-4f48-b358-250ce4e296de",
              "libraryUUID": None,
              "geo_tag_location": None,
              "buying_rate_profile": None,
              "energy_rate_profile": None,
              "buying_rate_profile_uuid": None,
              "energy_rate_profile_uuid": None,
              "allow_external_connection": False,
              "display_type": "InfiniteBus",
              "energy_sell_rate": 30.0,
              "energy_buy_rate": 12.0
            },
            {
              "name": "Community",
              "tags": None,
              "uuid": "a15bb9d1-8aa8-48e1-95f8-dfae11328b00",
              "children": [
                {
                  "name": "Home",
                  "tags": [
                    "Home"
                  ],
                  "uuid": "14f3e627-3ac5-4c42-9533-1b4d8c0a8653",
                  "children": [
                    {
                      "name": "PV",
                      "tilt": None,
                      "type": "PVProfile",
                      "uuid": "dfe49efc-c270-444a-a33c-3fa09bff3276",
                      "azimuth": None,
                      "libraryUUID": "06c63788-cc2f-4b1f-9f43-cfb355852d54",
                      "panel_count": 1,
                      "fit_to_limit": True,
                      "power_profile": "{\"filename\": \"Berlin_pv_1m.csv\"}",
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.817164413489536,
                        38.398776189002916
                      ],
                      "target_device_kpi": 0,
                      "final_selling_rate": 0.0,
                      "power_profile_uuid": "d8f9f372-d636-45da-a7f5-9ef02bbc8650",
                      "initial_selling_rate": 30.0,
                      "use_market_maker_rate": True,
                      "forecast_stream_enabled": None,
                      "allow_external_connection": None,
                      "energy_rate_decrease_per_update": None,
                      "display_type": "PV"
                    },
                    {
                      "name": "Load",
                      "type": "LoadProfile",
                      "uuid": "d1c2f12e-2ece-4354-a687-724a3f64d2fb",
                      "libraryUUID": "06c63788-cc2f-4b1f-9f43-cfb355852d54",
                      "fit_to_limit": True,
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.817164413489536,
                        38.398776189002916
                      ],
                      "final_buying_rate": 30.0,
                      "target_device_kpi": 0,
                      "daily_load_profile":
                      "{\"filename\": \"CHR27 Family both at work, 2 children HH1.csv\"}",
                      "initial_buying_rate": 0.0,
                      "use_market_maker_rate": True,
                      "daily_load_profile_uuid": "19c59878-511a-43c4-b808-fa66284634e7",
                      "forecast_stream_enabled": None,
                      "allow_external_connection": None,
                      "energy_rate_increase_per_update": None,
                      "display_type": "Load"
                    }
                  ],
                  "libraryUUID": None,
                  "geo_tag_location": [
                    21.817164413489536,
                    38.398776189002916
                  ],
                  "fit_area_boundary": True,
                  "grid_fee_constant": None,
                  "target_market_kpi": 0,
                  "export_capacity_kVA": None,
                  "grid_fee_percentage": None,
                  "import_capacity_kVA": None,
                  "allow_external_connection": True,
                  "baseline_peak_energy_export_kWh": None,
                  "baseline_peak_energy_import_kWh": None
                },
                {
                  "name": "Home 2",
                  "tags": [
                    "Home"
                  ],
                  "uuid": "733f68d1-18e2-464f-bc33-042804b55476",
                  "children": [
                    {
                      "name": "PV 2",
                      "tilt": None,
                      "type": "PVProfile",
                      "uuid": "0c5b9ce7-8b0a-426e-9c4c-926ff2e7c55d",
                      "azimuth": None,
                      "libraryUUID": "519f688a-48dd-4984-ae2f-bbdebcec7e6b",
                      "panel_count": 1,
                      "fit_to_limit": True,
                      "power_profile": "{\"filename\": \"Berlin_pv_1m.csv\"}",
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.819383035040943,
                        38.40110442451805
                      ],
                      "target_device_kpi": 0,
                      "final_selling_rate": 0.0,
                      "power_profile_uuid": "65517989-031d-465b-94f7-5889b1e6bcfa",
                      "initial_selling_rate": 30.0,
                      "use_market_maker_rate": True,
                      "forecast_stream_enabled": None,
                      "allow_external_connection": None,
                      "energy_rate_decrease_per_update": None,
                      "display_type": "PV"
                    },
                    {
                      "name": "Load 2",
                      "type": "LoadProfile",
                      "uuid": "cb012ba0-7df9-4f15-b321-1d0cbe04bbae",
                      "libraryUUID": "519f688a-48dd-4984-ae2f-bbdebcec7e6b",
                      "fit_to_limit": True,
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.819383035040943,
                        38.40110442451805
                      ],
                      "final_buying_rate": 30.0,
                      "target_device_kpi": 0,
                      "daily_load_profile":
                      "{\"filename\": \"CHR41 Family with 3 children, both at work HH1.csv\"}",
                      "initial_buying_rate": 0.0,
                      "use_market_maker_rate": True,
                      "daily_load_profile_uuid": "b4d2532e-02b6-4361-b0c6-b799de1731fe",
                      "forecast_stream_enabled": None,
                      "allow_external_connection": None,
                      "energy_rate_increase_per_update": None,
                      "display_type": "Load"
                    }
                  ],
                  "libraryUUID": None,
                  "geo_tag_location": [
                    21.819383035040943,
                    38.40110442451805
                  ],
                  "fit_area_boundary": True,
                  "grid_fee_constant": None,
                  "target_market_kpi": 0,
                  "export_capacity_kVA": None,
                  "grid_fee_percentage": None,
                  "import_capacity_kVA": None,
                  "allow_external_connection": True,
                  "baseline_peak_energy_export_kWh": None,
                  "baseline_peak_energy_import_kWh": None
                },
                {
                  "name": "Custom Load",
                  "type": "LoadHours",
                  "uuid": "cd3a108a-4eac-4f58-8d3a-e4f395a0aea4",
                  "address": None,
                  "avg_power_W": 100,
                  "capacity_kW": None,
                  "libraryUUID": None,
                  "fit_to_limit": True,
                  "update_interval": 1,
                  "geo_tag_location": [
                    21.816234162597056,
                    38.40017818882174
                  ],
                  "final_buying_rate": None,
                  "target_device_kpi": 0,
                  "initial_buying_rate": 0.0,
                  "use_market_maker_rate": True,
                  "forecast_stream_enabled": None,
                  "allow_external_connection": False,
                  "energy_rate_increase_per_update": None,
                  "display_type": "Load"
                },
                {
                  "name": "Home 3",
                  "tags": None,
                  "uuid": "4f012124-ebdc-43c0-a2c1-b5a39f966e8b",
                  "address": None,
                  "children": [
                    {
                      "name": "Custom Load 2",
                      "type": "LoadHours",
                      "uuid": "1bb73f37-1ea9-4e6e-95bf-f053cd66dd45",
                      "address": None,
                      "avg_power_W": 100,
                      "capacity_kW": None,
                      "libraryUUID": None,
                      "fit_to_limit": True,
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.81229703406487,
                        38.40119487732349
                      ],
                      "final_buying_rate": None,
                      "target_device_kpi": 0,
                      "initial_buying_rate": 0.0,
                      "use_market_maker_rate": True,
                      "forecast_stream_enabled": None,
                      "allow_external_connection": False,
                      "energy_rate_increase_per_update": None,
                      "display_type": "Load"
                    },
                    {
                      "name": "Battery",
                      "type": "Storage",
                      "uuid": "b30a4e3f-0eca-4284-be29-5b178ccd2e3e",
                      "address": None,
                      "initial_soc": 20.0,
                      "libraryUUID": None,
                      "fit_to_limit": True,
                      "min_allowed_soc": 3.0,
                      "update_interval": 1,
                      "geo_tag_location": [
                        21.81229703406487,
                        38.40119487732349
                      ],
                      "final_buying_rate": 22.0,
                      "target_device_kpi": 0,
                      "cap_price_strategy": False,
                      "final_selling_rate": 25.0,
                      "initial_buying_rate": 12.0,
                      "battery_capacity_kWh": 123.0,
                      "initial_selling_rate": 32.0,
                      "max_abs_battery_power_kW": 1432.2,
                      "allow_external_connection": False,
                      "energy_rate_decrease_per_update": None,
                      "energy_rate_increase_per_update": None,
                      "display_type": "Storage"
                    }
                  ],
                  "libraryUUID": None,
                  "feed_in_tariff": 0.0,
                  "geo_tag_location": [
                    21.81229703406487,
                    38.40119487732349
                  ],
                  "taxes_surcharges": 0.0,
                  "fit_area_boundary": True,
                  "fixed_monthly_fee": 0.0,
                  "grid_fee_constant": 1.0,
                  "market_maker_rate": 0.0,
                  "target_market_kpi": 0,
                  "export_capacity_kVA": 23.0,
                  "grid_fee_percentage": None,
                  "import_capacity_kVA": 1.0,
                  "coefficient_percentage": 0.0,
                  "marketplace_monthly_fee": 0.0,
                  "assistance_monthly_fee": 0.0,
                  "allow_external_connection": True,
                  "baseline_peak_energy_export_kWh": 43.0,
                  "baseline_peak_energy_import_kWh": 23.0
                },
                {
                  "name": "Battery 2",
                  "type": "Storage",
                  "uuid": "be655351-0574-48f0-864d-339bb67ba2fc",
                  "address": None,
                  "initial_soc": 20.0,
                  "libraryUUID": None,
                  "fit_to_limit": True,
                  "min_allowed_soc": 3.0,
                  "update_interval": 1,
                  "geo_tag_location": [
                    21.813921694708597,
                    38.39855216791665
                  ],
                  "final_buying_rate": 22.0,
                  "target_device_kpi": 0,
                  "cap_price_strategy": False,
                  "final_selling_rate": 25.0,
                  "initial_buying_rate": 12.0,
                  "battery_capacity_kWh": 123.0,
                  "initial_selling_rate": 32.0,
                  "max_abs_battery_power_kW": 1432.2,
                  "allow_external_connection": False,
                  "energy_rate_decrease_per_update": None,
                  "energy_rate_increase_per_update": None,
                  "display_type": "Storage"
                }
              ],
              "libraryUUID": None,
              "geo_tag_location": None,
              "fit_area_boundary": True,
              "grid_fee_constant": None,
              "target_market_kpi": 0,
              "export_capacity_kVA": None,
              "grid_fee_percentage": None,
              "import_capacity_kVA": None,
              "allow_external_connection": True,
              "baseline_peak_energy_export_kWh": None,
              "baseline_peak_energy_import_kWh": None
            }
          ],
          "libraryUUID": None,
          "geo_tag_location": None,
          "fit_area_boundary": True,
          "grid_fee_constant": None,
          "target_market_kpi": 0,
          "export_capacity_kVA": None,
          "grid_fee_percentage": None,
          "import_capacity_kVA": None,
          "allow_external_connection": True,
          "baseline_peak_energy_export_kWh": None,
          "baseline_peak_energy_import_kWh": None,
          "configuration_uuid": "b5ecdb78-e209-4af8-b8e9-d446440a9003"
        }

    def test_scenario_validator_works(self):
        validator = get_schema_validator("launch_simulation_scenario")
        is_valid, errors = validator.validate(self._data, True)
        assert not errors
        assert is_valid is True

    def test_scenario_serializer_works(self):
        serializer = get_schema_validator("launch_simulation_scenario")
        serialized_data = serializer.serialize(self._data, True)
        deserialized_data = serializer.deserialize(serialized_data)
        assert deserialized_data["name"] == "Grid"
        assert deserialized_data["tags"] is None
        assert deserialized_data["uuid"] == "bd867ebb-f3c8-4d8d-926a-a4181fa86c3a"
