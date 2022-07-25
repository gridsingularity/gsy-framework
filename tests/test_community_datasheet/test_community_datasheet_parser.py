import os
import pathlib
from copy import deepcopy
from unittest.mock import MagicMock, call, patch

import pytest

from gsy_framework.community_datasheet.community_datasheet_parser import (
    AssetCoordinatesBuilder, CommunityDatasheetParser)
from gsy_framework.community_datasheet.location_converter import LocationConverterException

FIXTURES_PATH = pathlib.Path(os.path.dirname(__file__)).parent / "fixtures"
BASE_MODULE = "gsy_framework.community_datasheet.community_datasheet_parser"


class TestCommunityDatasheetParser:

    @staticmethod
    @patch(f"{BASE_MODULE}.AssetCoordinatesBuilder", spec=True)
    @patch(
        "gsy_framework.community_datasheet.row_converters.uuid.uuid4", return_value="mocked-uuid")
    def test_parse(_uuid_mock, asset_coordinates_builder_cls_mock):
        filename = FIXTURES_PATH / "community_datasheet.xlsx"
        members_information = {
            "Member 1": {
                "email": "some-email-1@some-email.com",
                "zip_code": "64508",
                "address": "Am Werth 94, Wolffburg, Schleswig-Holstein, Germany",
                "market_maker_rate": 1,
                "feed_in_tariff": 7,
                "grid_fee_constant": 0.3,
                "taxes_surcharges": 0.5,
                "fixed_monthly_fee": 0.5,
                "marketplace_monthly_fee": 0.5,
                "coefficient_percentage": 0.5,
            },
            "Member 2": {
                "email": "some-email-2@some-email.com",
                "zip_code": "57441",
                "address": "Heisterbachstr. 8, Ost Colin, Hamburg, Germany",
                "market_maker_rate": 1,
                "feed_in_tariff": 7,
                "grid_fee_constant": 0.3,
                "taxes_surcharges": 0.5,
                "fixed_monthly_fee": 0.5,
                "marketplace_monthly_fee": 0.5,
                "coefficient_percentage": 0.5,
            },
        }

        # Assume that the AssetCoordinatesBuilder has filled the geo_tag_location correctly
        members_with_coordinates = deepcopy(members_information)
        members_with_coordinates["Member 1"]["geo_tag_location"] = (4.137182, 48.058159)
        members_with_coordinates["Member 2"]["geo_tag_location"] = (4.137182, 48.058159)

        asset_coordinates_builder_mock = MagicMock()
        asset_coordinates_builder_mock.get_member_coordinates.return_value = (4.137182, 48.058159)
        asset_coordinates_builder_cls_mock.return_value = asset_coordinates_builder_mock

        datasheet = CommunityDatasheetParser(filename=filename).parse()
        asset_coordinates_builder_mock.get_member_coordinates.assert_has_calls([
            call(members_with_coordinates["Member 1"]),
            call(members_with_coordinates["Member 2"])
            ]
        )
        assert datasheet.pvs == {
            "Member 1": [
                {
                    "name": "PV 1",
                    "type": "PV",
                    "uuid": "mocked-uuid",
                    "capacity_kW": 5,
                    "tilt": 12,
                    "azimuth": None,
                    "geo_tag_location": (4.137182, 48.058159),
                    "cloud_coverage": 4,
                    "power_profile": {
                        "2021-08-02T00:00": 11.5,
                        "2021-08-02T01:00": 11.5,
                        "2021-08-02T02:00": 11.5,
                        "2021-08-02T03:00": 11.5,
                        "2021-08-02T04:00": 11.5,
                        "2021-08-02T05:00": 11.5,
                        "2021-08-02T06:00": 11.5,
                        "2021-08-02T07:00": 11.5,
                        "2021-08-02T08:00": 11.5,
                        "2021-08-02T09:00": 11.5,
                        "2021-08-02T10:00": 11.5,
                        "2021-08-02T11:00": 11.5,
                        "2021-08-02T12:00": 11.5,
                        "2021-08-02T13:00": 11.5,
                        "2021-08-02T14:00": 11.5,
                        "2021-08-02T15:00": 11.5,
                        "2021-08-02T16:00": 0.0,
                    },
                }
            ],
            "Member 2": [
                {
                    "name": "PV 3",
                    "type": "PV",
                    "uuid": "mocked-uuid",
                    "capacity_kW": 12,
                    "tilt": 32,
                    "azimuth": 123,
                    "geo_tag_location": (4.137182, 48.058159),
                    "cloud_coverage": 5,
                }
            ],
        }

        assert datasheet.grid == {
            "name": "Grid Market",
            "allow_external_connection": False,
            "uuid": "mocked-uuid",
            "type": "Area",
            "children": [
                {
                    "name": "",
                    "allow_external_connection": False,
                    "uuid": "mocked-uuid",
                    "type": "InfiniteBus",
                    "energy_rate": 30,
                    "energy_buy_rate": 30,
                },
                {
                    "name": "Community",
                    "allow_external_connection": False,
                    "uuid": "mocked-uuid",
                    "type": "Area",
                    "children": [
                        {
                            "name": "Member 1",
                            "tags": ["Home"],
                            "type": "Area",
                            "uuid": "mocked-uuid",
                            "geo_tag_location": (4.137182, 48.058159),
                            "grid_fee_constant": 0.3,
                            "children": [
                                {
                                    "name": "Load 1",
                                    "type": "Load",
                                    "uuid": "mocked-uuid",
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "daily_load_profile": {
                                        "2021-08-02T00:00": 22.32,
                                        "2021-08-02T01:00": 20.72,
                                        "2021-08-02T02:00": 18.57,
                                        "2021-08-02T03:00": 0.0,
                                        "2021-08-02T04:00": 17.135,
                                        "2021-08-02T05:00": 15.927,
                                        "2021-08-02T06:00": 14.719,
                                        "2021-08-02T07:00": 13.511,
                                        "2021-08-02T08:00": 12.303,
                                        "2021-08-02T09:00": 11.095,
                                        "2021-08-02T10:00": 9.887,
                                        "2021-08-02T11:00": 8.679,
                                        "2021-08-02T12:00": 7.471,
                                        "2021-08-02T13:00": 6.263,
                                        "2021-08-02T14:00": 5.055,
                                        "2021-08-02T15:00": 3.847,
                                        "2021-08-02T16:00": 2.639,
                                    },
                                },
                                {
                                    "name": "PV 1",
                                    "type": "PV",
                                    "uuid": "mocked-uuid",
                                    "capacity_kW": 5,
                                    "tilt": 12,
                                    "azimuth": None,
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "cloud_coverage": 4,
                                    "power_profile": {
                                        "2021-08-02T00:00": 11.5,
                                        "2021-08-02T01:00": 11.5,
                                        "2021-08-02T02:00": 11.5,
                                        "2021-08-02T03:00": 11.5,
                                        "2021-08-02T04:00": 11.5,
                                        "2021-08-02T05:00": 11.5,
                                        "2021-08-02T06:00": 11.5,
                                        "2021-08-02T07:00": 11.5,
                                        "2021-08-02T08:00": 11.5,
                                        "2021-08-02T09:00": 11.5,
                                        "2021-08-02T10:00": 11.5,
                                        "2021-08-02T11:00": 11.5,
                                        "2021-08-02T12:00": 11.5,
                                        "2021-08-02T13:00": 11.5,
                                        "2021-08-02T14:00": 11.5,
                                        "2021-08-02T15:00": 11.5,
                                        "2021-08-02T16:00": 0.0,
                                    },
                                },
                                {
                                    "name": "Battery 1",
                                    "type": "Storage",
                                    "uuid": "mocked-uuid",
                                    "battery_capacity_kWh": 0.7,
                                    "min_allowed_soc": 10,
                                    "max_abs_battery_power_kW": 0.005,
                                    "geo_tag_location": (4.137182, 48.058159),
                                },
                            ],
                            "market_maker_rate": 1,
                            "feed_in_tariff": 7,
                            "taxes_surcharges": 0.5,
                            "fixed_monthly_fee": 0.5,
                            "marketplace_monthly_fee": 0.5,
                            "coefficient_percentage": 0.5,
                        },
                        {
                            "name": "Member 2",
                            "tags": ["Home"],
                            "type": "Area",
                            "uuid": "mocked-uuid",
                            "geo_tag_location": (4.137182, 48.058159),
                            "grid_fee_constant": 0.3,
                            "children": [
                                {
                                    "name": "PV 3",
                                    "type": "PV",
                                    "uuid": "mocked-uuid",
                                    "capacity_kW": 12,
                                    "tilt": 32,
                                    "azimuth": 123,
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "cloud_coverage": 5,
                                },
                                {
                                    "name": "Battery 2",
                                    "type": "Storage",
                                    "uuid": "mocked-uuid",
                                    "battery_capacity_kWh": 0.5,
                                    "min_allowed_soc": 10,
                                    "max_abs_battery_power_kW": 0.005,
                                    "geo_tag_location": (4.137182, 48.058159),
                                },
                            ],
                            "market_maker_rate": 1,
                            "feed_in_tariff": 7,
                            "taxes_surcharges": 0.5,
                            "fixed_monthly_fee": 0.5,
                            "marketplace_monthly_fee": 0.5,
                            "coefficient_percentage": 0.5,
                        },
                    ],
                },
            ],
        }


class TestAssetCoordinatesBuilder:
    @staticmethod
    @patch(f"{BASE_MODULE}.LocationConverter", spec=True)
    def test_get_member_coordinates(location_converter_class_mock):
        location_converter_instance = MagicMock()
        location_converter_instance.convert.return_value = (12, 10)
        location_converter_class_mock.return_value = location_converter_instance

        member_information = {
            "email": None,
            "zip_code": "1234",
            "address": "10210 La Loge-Pomblin, France",
            "market_maker_rate": 1,
            "feed_in_tariff": 7,
            "grid_fee_constant": None,
            "taxes": None,
            "fixed_fee": None,
            "marketplace_fee": None,
            "coefficient_percent": None,
        }
        coordinates_builder = AssetCoordinatesBuilder()
        results = coordinates_builder.get_member_coordinates(member_information)

        location_converter_instance.convert.assert_called_with(
            "10210 La Loge-Pomblin, France 1234")
        assert results == (12, 10)

    @staticmethod
    @patch(f"{BASE_MODULE}.LocationConverter", spec=True)
    def test_asset_coordinates_builder_raises_exceptions(location_converter_class_mock):
        """If instantiating the location converter causes an exception, it must be re-raised."""
        location_converter_class_mock.side_effect = LocationConverterException
        with pytest.raises(LocationConverterException):
            AssetCoordinatesBuilder()
