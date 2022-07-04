import os
import pathlib
from copy import deepcopy
from unittest.mock import MagicMock, patch

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
        pvs_by_member = {
            "Member 1": [
                {
                    "name": "PV 1", "type": "PV", "uuid": "mocked-uuid", "capacity_kW": 5,
                    "tilt": 12, "azimuth": None,
                }
            ],
            "Member 2": [
                {
                    "name": "PV 3", "type": "PV", "uuid": "mocked-uuid", "capacity_kW": 12,
                    "tilt": 32, "azimuth": 123,
                }
            ],
        }

        members_information = {
            "Member 1": {
                "email": "some-email-1@some-email.com",
                "zip_code": 64508,
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
                "zip_code": 57441,
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
        returned_pvs_by_member = deepcopy(pvs_by_member)
        returned_pvs_by_member["Member 1"][0]["geo_tag_location"] = (4.137182, 48.058159)
        returned_pvs_by_member["Member 2"][0]["geo_tag_location"] = (-3.1518571, 52.7885236)

        asset_coordinates_builder_mock = MagicMock()
        asset_coordinates_builder_mock.add_coordinates_to_assets.return_value = (
            returned_pvs_by_member)
        asset_coordinates_builder_cls_mock.return_value = asset_coordinates_builder_mock

        datasheet = CommunityDatasheetParser(filename=filename).parse()

        # import ipdb; ipdb.set_trace()
        asset_coordinates_builder_mock.add_coordinates_to_assets.assert_called_once_with(
            pvs_by_member, members_information)

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
                        "2021-08-02T00:15": 11.5,
                        "2021-08-02T00:30": 11.5,
                        "2021-08-02T00:44": 11.5,
                        "2021-08-02T00:59": 11.5,
                        "2021-08-02T01:14": 11.5,
                        "2021-08-02T01:29": 11.5,
                        "2021-08-02T01:44": 11.5,
                        "2021-08-02T01:59": 11.5,
                        "2021-08-02T02:14": 11.5,
                        "2021-08-02T02:29": 11.5,
                        "2021-08-02T02:44": 11.5,
                        "2021-08-02T02:59": 11.5,
                        "2021-08-02T03:14": 11.5,
                        "2021-08-02T03:29": 11.5,
                        "2021-08-02T03:44": 11.5,
                        "2021-08-02T03:59": 0.0,
                        "2021-08-02T04:14": 11.5,
                        "2021-08-02T04:29": 11.5,
                        "2021-08-02T04:44": 11.5,
                        "2021-08-02T04:59": 11.5,
                        "2021-08-02T05:14": 11.5,
                        "2021-08-02T05:29": 11.5,
                        "2021-08-02T05:44": 11.5,
                        "2021-08-02T05:59": 11.5,
                        "2021-08-02T06:14": 11.5,
                        "2021-08-02T06:29": 11.5,
                        "2021-08-02T06:44": 11.5,
                        "2021-08-02T06:59": 11.5,
                        "2021-08-02T07:14": 11.5,
                        "2021-08-02T07:29": 11.5,
                        "2021-08-02T07:44": 11.5,
                        "2021-08-02T07:59": 11.5,
                        "2021-08-02T08:14": 11.5,
                        "2021-08-02T08:29": 11.5,
                        "2021-08-02T08:44": 11.5,
                        "2021-08-02T08:59": 11.5,
                        "2021-08-02T09:14": 11.5,
                        "2021-08-02T09:29": 11.5,
                        "2021-08-02T09:44": 11.5,
                        "2021-08-02T09:59": 11.5,
                        "2021-08-02T10:14": 11.5,
                        "2021-08-02T10:29": 11.5,
                        "2021-08-02T10:44": 11.5,
                        "2021-08-02T10:59": 11.5,
                        "2021-08-02T11:14": 11.5,
                        "2021-08-02T11:29": 11.5,
                        "2021-08-02T11:44": 11.5,
                        "2021-08-02T11:59": 11.5,
                        "2021-08-02T12:14": 11.5,
                        "2021-08-02T12:29": 11.5,
                        "2021-08-02T12:44": 11.5,
                        "2021-08-02T12:59": 11.5,
                        "2021-08-02T13:14": 11.5,
                        "2021-08-02T13:29": 11.5,
                        "2021-08-02T13:44": 11.5,
                        "2021-08-02T13:59": 11.5,
                        "2021-08-02T14:14": 11.5,
                        "2021-08-02T14:29": 11.5,
                        "2021-08-02T14:44": 11.5,
                        "2021-08-02T14:59": 11.5,
                        "2021-08-02T15:14": 11.5,
                        "2021-08-02T15:29": 11.5,
                        "2021-08-02T15:44": 11.5,
                        "2021-08-02T15:59": 11.5,
                        "2021-08-02T16:14": 11.5,
                        "2021-08-02T16:29": 11.5,
                        "2021-08-02T16:44": 11.5,
                        "2021-08-02T16:59": 11.5,
                        "2021-08-02T17:14": 11.5,
                        "2021-08-02T17:29": 11.5,
                        "2021-08-02T17:44": 11.5,
                        "2021-08-02T17:59": 11.5,
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
                    "geo_tag_location": (-3.1518571, 52.7885236),
                    "cloud_coverage": 5,
                }
            ],
        }

        assert datasheet.grid == {
            "name": "Community",
            "tags": None,
            "type": "Area",
            "uuid": "mocked-uuid",
            "children": [
                {
                    "name": "Member 1",
                    "tags": ["Home"],
                    "type": "Area",
                    "uuid": "mocked-uuid",
                    "grid_fee_constant": 0.3,
                    "children": [
                        {
                            "name": "Load 1",
                            "type": "Load",
                            "uuid": "mocked-uuid",
                            "daily_load_profile": {
                                "2021-08-02T00:00": 22.32,
                                "2021-08-02T00:15": 20.72,
                                "2021-08-02T00:30": 18.57,
                                "2021-08-02T00:44": 0.0,
                                "2021-08-02T00:59": 17.135,
                                "2021-08-02T01:14": 15.927,
                                "2021-08-02T01:29": 14.719,
                                "2021-08-02T01:44": 13.511,
                                "2021-08-02T01:59": 12.303,
                                "2021-08-02T02:14": 11.095,
                                "2021-08-02T02:29": 9.887,
                                "2021-08-02T02:44": 8.679,
                                "2021-08-02T02:59": 7.471,
                                "2021-08-02T03:14": 6.263,
                                "2021-08-02T03:29": 5.055,
                                "2021-08-02T03:44": 3.847,
                                "2021-08-02T03:59": 2.639,
                                "2021-08-02T04:14": 1.431,
                                "2021-08-02T04:29": 0.223000000000003,
                                "2021-08-02T04:44": -0.984999999999999,
                                "2021-08-02T04:59": -2.193,
                                "2021-08-02T05:14": -3.401,
                                "2021-08-02T05:29": -4.609,
                                "2021-08-02T05:44": -5.817,
                                "2021-08-02T05:59": -7.025,
                                "2021-08-02T06:14": -8.233,
                                "2021-08-02T06:29": -9.441,
                                "2021-08-02T06:44": -10.649,
                                "2021-08-02T06:59": -11.857,
                                "2021-08-02T07:14": -13.065,
                                "2021-08-02T07:29": -14.273,
                                "2021-08-02T07:44": -15.481,
                                "2021-08-02T07:59": -16.689,
                                "2021-08-02T08:14": -17.897,
                                "2021-08-02T08:29": -19.105,
                                "2021-08-02T08:44": -20.313,
                                "2021-08-02T08:59": -21.521,
                                "2021-08-02T09:14": -22.729,
                                "2021-08-02T09:29": -23.937,
                                "2021-08-02T09:44": -25.145,
                                "2021-08-02T09:59": -26.353,
                                "2021-08-02T10:14": -27.561,
                                "2021-08-02T10:29": -28.769,
                                "2021-08-02T10:44": -29.977,
                                "2021-08-02T10:59": -31.185,
                                "2021-08-02T11:14": -32.393,
                                "2021-08-02T11:29": -33.601,
                                "2021-08-02T11:44": -34.809,
                                "2021-08-02T11:59": -36.017,
                                "2021-08-02T12:14": -37.225,
                                "2021-08-02T12:29": -38.433,
                                "2021-08-02T12:44": -39.641,
                                "2021-08-02T12:59": -40.849,
                                "2021-08-02T13:14": -42.057,
                                "2021-08-02T13:29": -43.265,
                                "2021-08-02T13:44": -44.473,
                                "2021-08-02T13:59": -45.681,
                                "2021-08-02T14:14": -46.889,
                                "2021-08-02T14:29": -48.097,
                                "2021-08-02T14:44": -49.305,
                                "2021-08-02T14:59": -50.513,
                                "2021-08-02T15:14": -51.721,
                                "2021-08-02T15:29": -52.929,
                                "2021-08-02T15:44": -54.137,
                                "2021-08-02T15:59": -55.345,
                                "2021-08-02T16:14": -56.553,
                                "2021-08-02T16:29": -57.761,
                                "2021-08-02T16:44": -58.969,
                                "2021-08-02T16:59": -60.177,
                                "2021-08-02T17:14": -61.385,
                                "2021-08-02T17:29": -62.593,
                                "2021-08-02T17:44": -63.801,
                                "2021-08-02T17:59": -65.009,
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
                                "2021-08-02T00:15": 11.5,
                                "2021-08-02T00:30": 11.5,
                                "2021-08-02T00:44": 11.5,
                                "2021-08-02T00:59": 11.5,
                                "2021-08-02T01:14": 11.5,
                                "2021-08-02T01:29": 11.5,
                                "2021-08-02T01:44": 11.5,
                                "2021-08-02T01:59": 11.5,
                                "2021-08-02T02:14": 11.5,
                                "2021-08-02T02:29": 11.5,
                                "2021-08-02T02:44": 11.5,
                                "2021-08-02T02:59": 11.5,
                                "2021-08-02T03:14": 11.5,
                                "2021-08-02T03:29": 11.5,
                                "2021-08-02T03:44": 11.5,
                                "2021-08-02T03:59": 0.0,
                                "2021-08-02T04:14": 11.5,
                                "2021-08-02T04:29": 11.5,
                                "2021-08-02T04:44": 11.5,
                                "2021-08-02T04:59": 11.5,
                                "2021-08-02T05:14": 11.5,
                                "2021-08-02T05:29": 11.5,
                                "2021-08-02T05:44": 11.5,
                                "2021-08-02T05:59": 11.5,
                                "2021-08-02T06:14": 11.5,
                                "2021-08-02T06:29": 11.5,
                                "2021-08-02T06:44": 11.5,
                                "2021-08-02T06:59": 11.5,
                                "2021-08-02T07:14": 11.5,
                                "2021-08-02T07:29": 11.5,
                                "2021-08-02T07:44": 11.5,
                                "2021-08-02T07:59": 11.5,
                                "2021-08-02T08:14": 11.5,
                                "2021-08-02T08:29": 11.5,
                                "2021-08-02T08:44": 11.5,
                                "2021-08-02T08:59": 11.5,
                                "2021-08-02T09:14": 11.5,
                                "2021-08-02T09:29": 11.5,
                                "2021-08-02T09:44": 11.5,
                                "2021-08-02T09:59": 11.5,
                                "2021-08-02T10:14": 11.5,
                                "2021-08-02T10:29": 11.5,
                                "2021-08-02T10:44": 11.5,
                                "2021-08-02T10:59": 11.5,
                                "2021-08-02T11:14": 11.5,
                                "2021-08-02T11:29": 11.5,
                                "2021-08-02T11:44": 11.5,
                                "2021-08-02T11:59": 11.5,
                                "2021-08-02T12:14": 11.5,
                                "2021-08-02T12:29": 11.5,
                                "2021-08-02T12:44": 11.5,
                                "2021-08-02T12:59": 11.5,
                                "2021-08-02T13:14": 11.5,
                                "2021-08-02T13:29": 11.5,
                                "2021-08-02T13:44": 11.5,
                                "2021-08-02T13:59": 11.5,
                                "2021-08-02T14:14": 11.5,
                                "2021-08-02T14:29": 11.5,
                                "2021-08-02T14:44": 11.5,
                                "2021-08-02T14:59": 11.5,
                                "2021-08-02T15:14": 11.5,
                                "2021-08-02T15:29": 11.5,
                                "2021-08-02T15:44": 11.5,
                                "2021-08-02T15:59": 11.5,
                                "2021-08-02T16:14": 11.5,
                                "2021-08-02T16:29": 11.5,
                                "2021-08-02T16:44": 11.5,
                                "2021-08-02T16:59": 11.5,
                                "2021-08-02T17:14": 11.5,
                                "2021-08-02T17:29": 11.5,
                                "2021-08-02T17:44": 11.5,
                                "2021-08-02T17:59": 11.5,
                            },
                        },
                        {
                            "name": "Battery 1",
                            "type": "Storage",
                            "uuid": "mocked-uuid",
                            "battery_capacity_kWh": 0.7,
                            "min_allowed_soc": 10,
                            "max_abs_battery_power_kW": 0.005,
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
                    "grid_fee_constant": 0.3,
                    "children": [
                        {
                            "name": "PV 3",
                            "type": "PV",
                            "uuid": "mocked-uuid",
                            "capacity_kW": 12,
                            "tilt": 32,
                            "azimuth": 123,
                            "geo_tag_location": (-3.1518571, 52.7885236),
                            "cloud_coverage": 5,
                        },
                        {
                            "name": "Battery 2",
                            "type": "Storage",
                            "uuid": "mocked-uuid",
                            "battery_capacity_kWh": 0.5,
                            "min_allowed_soc": 13,
                            "max_abs_battery_power_kW": 0.005,
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
        }


class TestAssetCoordinatesBuilder:
    @staticmethod
    @patch(f"{BASE_MODULE}.LocationConverter", spec=True)
    def test_add_coordinates_to_assets(location_converter_class_mock):
        location_converter_instance = MagicMock()
        location_converter_instance.convert.return_value = (12, 10)
        location_converter_class_mock.return_value = location_converter_instance

        coordinates_builder = AssetCoordinatesBuilder()
        assets_by_member = {
            "Member 1": [
                {"name": "Load 1", "type": "Load", "uuid": "load-uuid"},
                {"name": "PV 1", "type": "PV", "uuid": "pv-uuid"}
            ],
            "Member 2": [
                {"name": "Load 2", "type": "Load", "uuid": "load2-uuid"},
                {"name": "PV 2", "type": "PV", "uuid": "pv2-uuid"}
            ],
        }
        members_information = {
            "Member 1": {
                "email": None,
                "zip_code": None,
                "address": "10210 La Loge-Pomblin, France",
                "market_maker_rate": 1,
                "feed_in_tariff": 7,
                "grid_fee_constant": None,
                "taxes": None,
                "fixed_fee": None,
                "marketplace_fee": None,
                "coefficient_percent": None,
            },
            "Member 2": {
                "email": None,
                "zip_code": None,
                "address": "Carreg Winllan",
                "market_maker_rate": 1,
                "feed_in_tariff": 7,
                "grid_fee_constant": None,
                "taxes": None,
                "fixed_fee": None,
                "marketplace_fee": None,
                "coefficient_percent": None,
            }
        }
        results = coordinates_builder.add_coordinates_to_assets(
            assets_by_member, members_information)

        assert results == {
            "Member 1": [
                {
                    "name": "Load 1",
                    "type": "Load",
                    "uuid": "load-uuid",
                    "geo_tag_location": (12, 10),
                },
                {
                    "name": "PV 1",
                    "type": "PV",
                    "uuid": "pv-uuid",
                    "geo_tag_location": (12, 10),
                }
            ],
            "Member 2": [
                {
                    "name": "Load 2",
                    "type": "Load",
                    "uuid": "load2-uuid",
                    "geo_tag_location": (12, 10),
                },
                {
                    "name": "PV 2",
                    "type": "PV",
                    "uuid": "pv2-uuid",
                    "geo_tag_location": (12, 10),
                },
            ]
        }

    @staticmethod
    @patch(f"{BASE_MODULE}.LocationConverter", spec=True)
    def test_asset_coordinates_builder_raises_exceptions(location_converter_class_mock):
        """If instantiating the location converter causes an exception, it must be re-raised."""
        location_converter_class_mock.side_effect = LocationConverterException
        with pytest.raises(LocationConverterException):
            AssetCoordinatesBuilder()
