from gsy_framework.schema.validators import get_schema_validator


class TestScenarioValidator:

    def setup_method(self):
        self._data = {
            'name': 'Grid Market',
            'tags': None,
            'uuid': 'f27e8ad9-0436-4d8f-ae6f-7163e2e83607',
            'address': None,
            'children': [
                {
                    'name': '',
                    'type': 'InfiniteBus',
                    'uuid': '5723d08c-2869-4dc8-9501-86cb7b80f69e',
                    'address': None,
                    'libraryUUID': None,
                    'geo_tag_location': None,
                    'buying_rate_profile': None,
                    'energy_rate_profile': None,
                    'buying_rate_profile_uuid': None,
                    'energy_rate_profile_uuid': None,
                    'allow_external_connection': False,
                    'display_type': 'InfiniteBus',
                    'energy_sell_rate': 30.0,
                    'energy_buy_rate': 0.0
                },
                # {
                #     'name': 'Community',
                #     'tags': [
                #         'Home'
                #     ],
                #     'uuid': '77a06926-1621-4637-856c-98d1f1f0beab',
                #     'address': None,
                #     'children': [
                #         {
                #             'name': 'Custom PV',
                #             'tilt': 0.0,
                #             'type': 'PVProfile',
                #             'uuid': 'ed5a2988-4cd6-456d-b18b-d747df7dafe3',
                #             'address': None,
                #             'azimuth': 0.0,
                #             'libraryUUID': None,
                #             'panel_count': 1,
                #             'fit_to_limit': True,
                #             'power_profile':
                #                 '{"filename": "rebase_ed5a2988-4cd6-456d-b18b-d747df7dafe3"}',
                #             'cloud_coverage': 5,
                #             'update_interval': 1,
                #             'geo_tag_location': [
                #                 20.985962,
                #                 39.157855
                #             ],
                #             'target_device_kpi': 0,
                #             'final_selling_rate': 0.0,
                #             'power_profile_uuid': '3e779035-67c7-448f-828a-613af8da2d95',
                #             'initial_selling_rate': None,
                #             'use_market_maker_rate': True,
                #             'forecast_stream_enabled': None,
                #             'allow_external_connection': False,
                #             'energy_rate_decrease_per_update': None,
                #             'display_type': 'PV'
                #         },
                #         {
                #             'name': 'Custom PV 2',
                #             'tilt': 0.0,
                #             'type': 'PVProfile',
                #             'uuid': '7549fd94-3ee4-4871-bc9d-f60e87b5c9f4',
                #             'address': None,
                #             'azimuth': 0.0,
                #             'libraryUUID': None,
                #             'panel_count': 1,
                #             'fit_to_limit': True,
                #             'power_profile':
                #                 '{"filename": "rebase_7549fd94-3ee4-4871-bc9d-f60e87b5c9f4"}',
                #             'cloud_coverage': 5,
                #             'update_interval': 1,
                #             'geo_tag_location': [
                #                 20.987989565002465,
                #                 39.159748086619146
                #             ],
                #             'target_device_kpi': 0,
                #             'final_selling_rate': 0.0,
                #             'power_profile_uuid': '07b2ba6d-6ecc-4556-99e5-5febeec9362b',
                #             'initial_selling_rate': None,
                #             'use_market_maker_rate': True,
                #             'forecast_stream_enabled': None,
                #             'allow_external_connection': False,
                #             'energy_rate_decrease_per_update': None,
                #             'display_type': 'PV'
                #         }
                #     ],
                #     'libraryUUID': None,
                #     'feed_in_tariff': None,
                #     'geo_tag_location': None,
                #     'taxes_surcharges': 0.0,
                #     'fit_area_boundary': True,
                #     'fixed_monthly_fee': 0.0,
                #     'grid_fee_constant': None,
                #     'market_maker_rate': None,
                #     'target_market_kpi': 0,
                #     'export_capacity_kVA': None,
                #     'grid_fee_percentage': None,
                #     'import_capacity_kVA': None,
                #     'coefficient_percentage': 0.0,
                #     'marketplace_monthly_fee': 0.0,
                #     'allow_external_connection': True,
                #     'baseline_peak_energy_export_kWh': None,
                #     'baseline_peak_energy_import_kWh': None
                # }
            ],
            'libraryUUID': None,
            'feed_in_tariff': None,
            'geo_tag_location': None,
            'taxes_surcharges': 0.0,
            'fit_area_boundary': True,
            'fixed_monthly_fee': 0.0,
            'grid_fee_constant': None,
            'market_maker_rate': None,
            'target_market_kpi': 0,
            'export_capacity_kVA': None,
            'grid_fee_percentage': None,
            'import_capacity_kVA': None,
            'coefficient_percentage': 0.0,
            'marketplace_monthly_fee': 0.0,
            'allow_external_connection': True,
            'baseline_peak_energy_export_kWh': None,
            'baseline_peak_energy_import_kWh': None,
            'configuration_uuid': '54c8fd14-06d8-4c1d-9977-a08f37e10436'
        }

    def test_scenario_validator_works(self):
        validator = get_schema_validator("launch_simulation_scenario")
        is_valid, errors = validator.validate(self._data, True)
        print(errors)
        assert is_valid is True
