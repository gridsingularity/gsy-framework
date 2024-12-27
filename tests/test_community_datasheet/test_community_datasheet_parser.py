import os
import pathlib
from copy import deepcopy
from datetime import timedelta
from unittest.mock import MagicMock, call, patch

import pytest

from gsy_framework.community_datasheet.community_datasheet_parser import (
    CommunityDatasheetParser,
    DefaultCommunityAreaNames,
)
from gsy_framework.community_datasheet.location_converter import LocationConverterException
from gsy_framework.community_datasheet.row_converters import AssetCoordinatesBuilder
from gsy_framework.constants_limits import DATE_TIME_FORMAT
from gsy_framework.default_cds_downloader import DefaultCDSDownloader

FIXTURES_PATH = pathlib.Path(os.path.dirname(__file__)).parent / "fixtures"
BASE_MODULE = "gsy_framework.community_datasheet.row_converters"


class TestCommunityDatasheetParser:

    @staticmethod
    @patch(f"{BASE_MODULE}.AssetCoordinatesBuilder", spec=True)
    @patch(
        "gsy_framework.community_datasheet.row_converters.uuid.uuid4", return_value="mocked-uuid"
    )
    def test_parse(_uuid_mock, asset_coordinates_builder_cls_mock):
        cds_file_downloader = DefaultCDSDownloader()
        cds_file_downloader.download()
        cds_filename = cds_file_downloader.cds_file_path
        members_information = {
            "Home 1": {
                "email": "some-email-1@some-email.com",
                "zip_code": "10965",
                "address": "Berlin, Germany",
                "market_maker_rate": 0.3,
                "feed_in_tariff": 0.07,
                "grid_import_fee_const": 0.075,
                "grid_export_fee_const": 0.0,
                "taxes_surcharges": 0.15,
                "electricity_tax": 0.0,
                "fixed_monthly_fee": 0.5,
                "marketplace_monthly_fee": 0.5,
                "assistance_monthly_fee": 0.0,
                "service_monthly_fee": 0.0,
                "coefficient_percentage": 0.5,
                "uuid": "mocked-uuid",
                "asset_count": 2,
            },
            "Home 2": {
                "email": "some-email-2@some-email.com",
                "zip_code": "14532",
                "address": "Kleinmachnow",
                "market_maker_rate": 0.3,
                "feed_in_tariff": 0.07,
                "grid_import_fee_const": 0.075,
                "grid_export_fee_const": 0.0,
                "taxes_surcharges": 0.15,
                "electricity_tax": 0.0,
                "fixed_monthly_fee": 0.5,
                "marketplace_monthly_fee": 0.5,
                "assistance_monthly_fee": 0.0,
                "service_monthly_fee": 0.0,
                "coefficient_percentage": 0.3,
                "uuid": "mocked-uuid",
                "asset_count": 1,
            },
            "Home 3": {
                "email": "some-email-3@some-email.com",
                "zip_code": "12099",
                "address": "Berlin, Germany",
                "market_maker_rate": 0.3,
                "feed_in_tariff": 0.07,
                "grid_import_fee_const": 0.075,
                "grid_export_fee_const": 0.0,
                "taxes_surcharges": 0.15,
                "electricity_tax": 0.0,
                "fixed_monthly_fee": 0.5,
                "marketplace_monthly_fee": 0.5,
                "assistance_monthly_fee": 0.0,
                "service_monthly_fee": 0.0,
                "coefficient_percentage": 0.2,
                "uuid": "mocked-uuid",
                "asset_count": 1,
            },
        }

        # Assume that the AssetCoordinatesBuilder has filled the geo_tag_location correctly
        members_with_coordinates = deepcopy(members_information)
        members_with_coordinates["Home 1"]["geo_tag_location"] = (4.137182, 48.058159)
        members_with_coordinates["Home 2"]["geo_tag_location"] = (4.137182, 48.058159)
        members_with_coordinates["Home 3"]["geo_tag_location"] = (4.137182, 48.058159)

        asset_coordinates_builder_mock = MagicMock()
        asset_coordinates_builder_mock.get_member_coordinates.return_value = (4.137182, 48.058159)
        asset_coordinates_builder_cls_mock.return_value = asset_coordinates_builder_mock

        datasheet = CommunityDatasheetParser(filename=cds_filename).parse()
        address_dict_1 = {
            "address": members_with_coordinates["Home 1"]["address"],
            "zip_code": members_with_coordinates["Home 1"]["zip_code"],
        }
        address_dict_2 = {
            "address": members_with_coordinates["Home 2"]["address"],
            "zip_code": members_with_coordinates["Home 2"]["zip_code"],
        }
        address_dict_3 = {
            "address": members_with_coordinates["Home 3"]["address"],
            "zip_code": members_with_coordinates["Home 3"]["zip_code"],
        }
        asset_coordinates_builder_mock.get_member_coordinates.assert_has_calls(
            [call(address_dict_1), call(address_dict_2), call(address_dict_3)]
        )
        assert datasheet.pvs == {
            "Home 1": [
                {
                    "name": "PV 1",
                    "type": "PV",
                    "uuid": "mocked-uuid",
                    "capacity_kW": 12,
                    "tilt": 12,
                    "azimuth": 180,
                    "geo_tag_location": (4.137182, 48.058159),
                    "cloud_coverage": 5,
                }
            ]
        }

        expected_member_dict = deepcopy(members_with_coordinates)
        for member_name in ["Home 1", "Home 2", "Home 3"]:
            expected_member_dict[member_name]["grid_export_fee_const"] = 0
            expected_member_dict[member_name]["name"] = ""
            expected_member_dict[member_name]["service_monthly_fee"] = 0.0
            expected_member_dict[member_name]["contracted_power_monthly_fee"] = 0.0
            expected_member_dict[member_name]["contracted_power_cargo_monthly_fee"] = 0.0
            expected_member_dict[member_name]["energy_cargo_fee"] = 0.0

        assert datasheet.members == expected_member_dict
        assert datasheet.grid == {
            "name": DefaultCommunityAreaNames.GRID.value,
            "allow_external_connection": False,
            "uuid": "mocked-uuid",
            "type": "Area",
            "children": [
                {
                    "name": DefaultCommunityAreaNames.INFINITE_BUS.value,
                    "allow_external_connection": False,
                    "uuid": "mocked-uuid",
                    "type": "InfiniteBus",
                    "energy_rate": 30,
                    "energy_buy_rate": 30,
                },
                {
                    "name": DefaultCommunityAreaNames.COMMUNITY.value,
                    "allow_external_connection": False,
                    "uuid": "mocked-uuid",
                    "type": "Area",
                    "children": [
                        {
                            "name": "Home 1",
                            "tags": ["Home"],
                            "type": "Area",
                            "uuid": "mocked-uuid",
                            "geo_tag_location": (4.137182, 48.058159),
                            "address": "Berlin, Germany",
                            "children": [
                                {
                                    "name": "Load 1",
                                    "type": "Load",
                                    "uuid": "mocked-uuid",
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "daily_load_profile": {
                                        "2021-01-25T00:00": 0.1,
                                        "2021-01-25T00:15": 0.1,
                                        "2021-01-25T00:30": 0.1,
                                        "2021-01-25T00:45": 0.1,
                                        "2021-01-25T01:00": 0.1,
                                        "2021-01-25T01:15": 0.1,
                                        "2021-01-25T01:30": 0.1,
                                        "2021-01-25T01:45": 0.1,
                                        "2021-01-25T02:00": 0.1,
                                        "2021-01-25T02:15": 0.1,
                                        "2021-01-25T02:30": 0.1,
                                        "2021-01-25T02:45": 0.1,
                                        "2021-01-25T03:00": 0.1,
                                        "2021-01-25T03:15": 0.1,
                                        "2021-01-25T03:30": 0.1,
                                        "2021-01-25T03:45": 0.1,
                                        "2021-01-25T04:00": 0.1,
                                        "2021-01-25T04:15": 0.1,
                                        "2021-01-25T04:30": 0.1,
                                        "2021-01-25T04:45": 0.1,
                                        "2021-01-25T05:00": 0.1,
                                        "2021-01-25T05:15": 0.1,
                                        "2021-01-25T05:30": 0.1,
                                        "2021-01-25T05:45": 0.1,
                                        "2021-01-25T06:00": 0.1,
                                        "2021-01-25T06:15": 0.1,
                                        "2021-01-25T06:30": 0.1,
                                        "2021-01-25T06:45": 0.1,
                                        "2021-01-25T07:00": 0.1,
                                        "2021-01-25T07:15": 0.1,
                                        "2021-01-25T07:30": 0.1,
                                        "2021-01-25T07:45": 0.1,
                                        "2021-01-25T08:00": 0.1,
                                        "2021-01-25T08:15": 0.1,
                                        "2021-01-25T08:30": 0.1,
                                        "2021-01-25T08:45": 0.1,
                                        "2021-01-25T09:00": 0.1,
                                        "2021-01-25T09:15": 0.1,
                                        "2021-01-25T09:30": 0.1,
                                        "2021-01-25T09:45": 0.1,
                                        "2021-01-25T10:00": 0.1,
                                        "2021-01-25T10:15": 0.1,
                                        "2021-01-25T10:30": 0.1,
                                        "2021-01-25T10:45": 0.1,
                                        "2021-01-25T11:00": 0.1,
                                        "2021-01-25T11:15": 0.1,
                                        "2021-01-25T11:30": 0.1,
                                        "2021-01-25T11:45": 0.1,
                                        "2021-01-25T12:00": 0.1,
                                        "2021-01-25T12:15": 0.1,
                                        "2021-01-25T12:30": 0.1,
                                        "2021-01-25T12:45": 0.1,
                                        "2021-01-25T13:00": 0.1,
                                        "2021-01-25T13:15": 0.1,
                                        "2021-01-25T13:30": 0.1,
                                        "2021-01-25T13:45": 0.1,
                                        "2021-01-25T14:00": 0.1,
                                        "2021-01-25T14:15": 0.1,
                                        "2021-01-25T14:30": 0.1,
                                        "2021-01-25T14:45": 0.1,
                                        "2021-01-25T15:00": 0.1,
                                        "2021-01-25T15:15": 0.1,
                                        "2021-01-25T15:30": 0.1,
                                        "2021-01-25T15:45": 0.1,
                                        "2021-01-25T16:00": 0.1,
                                        "2021-01-25T16:15": 0.1,
                                        "2021-01-25T16:30": 0.1,
                                        "2021-01-25T16:45": 0.1,
                                        "2021-01-25T17:00": 0.1,
                                        "2021-01-25T17:15": 0.1,
                                        "2021-01-25T17:30": 0.1,
                                        "2021-01-25T17:45": 0.1,
                                        "2021-01-25T18:00": 0.1,
                                        "2021-01-25T18:15": 0.1,
                                        "2021-01-25T18:30": 0.1,
                                        "2021-01-25T18:45": 0.1,
                                        "2021-01-25T19:00": 0.1,
                                        "2021-01-25T19:15": 0.1,
                                        "2021-01-25T19:30": 0.1,
                                        "2021-01-25T19:45": 0.1,
                                        "2021-01-25T20:00": 0.1,
                                        "2021-01-25T20:15": 0.1,
                                        "2021-01-25T20:30": 0.1,
                                        "2021-01-25T20:45": 0.1,
                                        "2021-01-25T21:00": 0.1,
                                        "2021-01-25T21:15": 0.1,
                                        "2021-01-25T21:30": 0.1,
                                        "2021-01-25T21:45": 0.1,
                                        "2021-01-25T22:00": 0.1,
                                        "2021-01-25T22:15": 0.1,
                                        "2021-01-25T22:30": 0.1,
                                        "2021-01-25T22:45": 0.1,
                                        "2021-01-25T23:00": 0.1,
                                        "2021-01-25T23:15": 0.1,
                                        "2021-01-25T23:30": 0.1,
                                        "2021-01-25T23:45": 0.1,
                                    },
                                },
                                {
                                    "name": "PV 1",
                                    "type": "PV",
                                    "uuid": "mocked-uuid",
                                    "capacity_kW": 12,
                                    "tilt": 12,
                                    "azimuth": 180,
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "cloud_coverage": 5,
                                },
                            ],
                        },
                        {
                            "name": "Home 2",
                            "tags": ["Home"],
                            "type": "Area",
                            "uuid": "mocked-uuid",
                            "geo_tag_location": (4.137182, 48.058159),
                            "address": "Kleinmachnow",
                            "children": [
                                {
                                    "name": "Load 2",
                                    "type": "Load",
                                    "uuid": "mocked-uuid",
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "daily_load_profile": {
                                        "2021-01-25T00:00": 0.1,
                                        "2021-01-25T00:15": 0.1,
                                        "2021-01-25T00:30": 0.1,
                                        "2021-01-25T00:45": 0.1,
                                        "2021-01-25T01:00": 0.1,
                                        "2021-01-25T01:15": 0.1,
                                        "2021-01-25T01:30": 0.1,
                                        "2021-01-25T01:45": 0.1,
                                        "2021-01-25T02:00": 0.1,
                                        "2021-01-25T02:15": 0.1,
                                        "2021-01-25T02:30": 0.1,
                                        "2021-01-25T02:45": 0.1,
                                        "2021-01-25T03:00": 0.1,
                                        "2021-01-25T03:15": 0.1,
                                        "2021-01-25T03:30": 0.1,
                                        "2021-01-25T03:45": 0.1,
                                        "2021-01-25T04:00": 0.1,
                                        "2021-01-25T04:15": 0.1,
                                        "2021-01-25T04:30": 0.1,
                                        "2021-01-25T04:45": 0.1,
                                        "2021-01-25T05:00": 0.1,
                                        "2021-01-25T05:15": 0.1,
                                        "2021-01-25T05:30": 0.1,
                                        "2021-01-25T05:45": 0.1,
                                        "2021-01-25T06:00": 0.1,
                                        "2021-01-25T06:15": 0.1,
                                        "2021-01-25T06:30": 0.1,
                                        "2021-01-25T06:45": 0.1,
                                        "2021-01-25T07:00": 0.1,
                                        "2021-01-25T07:15": 0.1,
                                        "2021-01-25T07:30": 0.1,
                                        "2021-01-25T07:45": 0.1,
                                        "2021-01-25T08:00": 0.1,
                                        "2021-01-25T08:15": 0.1,
                                        "2021-01-25T08:30": 0.1,
                                        "2021-01-25T08:45": 0.1,
                                        "2021-01-25T09:00": 0.1,
                                        "2021-01-25T09:15": 0.1,
                                        "2021-01-25T09:30": 0.1,
                                        "2021-01-25T09:45": 0.1,
                                        "2021-01-25T10:00": 0.1,
                                        "2021-01-25T10:15": 0.1,
                                        "2021-01-25T10:30": 0.1,
                                        "2021-01-25T10:45": 0.1,
                                        "2021-01-25T11:00": 0.1,
                                        "2021-01-25T11:15": 0.1,
                                        "2021-01-25T11:30": 0.1,
                                        "2021-01-25T11:45": 0.1,
                                        "2021-01-25T12:00": 0.1,
                                        "2021-01-25T12:15": 0.1,
                                        "2021-01-25T12:30": 0.1,
                                        "2021-01-25T12:45": 0.1,
                                        "2021-01-25T13:00": 0.1,
                                        "2021-01-25T13:15": 0.1,
                                        "2021-01-25T13:30": 0.1,
                                        "2021-01-25T13:45": 0.1,
                                        "2021-01-25T14:00": 0.1,
                                        "2021-01-25T14:15": 0.1,
                                        "2021-01-25T14:30": 0.1,
                                        "2021-01-25T14:45": 0.1,
                                        "2021-01-25T15:00": 0.1,
                                        "2021-01-25T15:15": 0.1,
                                        "2021-01-25T15:30": 0.1,
                                        "2021-01-25T15:45": 0.1,
                                        "2021-01-25T16:00": 0.1,
                                        "2021-01-25T16:15": 0.1,
                                        "2021-01-25T16:30": 0.1,
                                        "2021-01-25T16:45": 0.1,
                                        "2021-01-25T17:00": 0.1,
                                        "2021-01-25T17:15": 0.1,
                                        "2021-01-25T17:30": 0.1,
                                        "2021-01-25T17:45": 0.1,
                                        "2021-01-25T18:00": 0.1,
                                        "2021-01-25T18:15": 0.1,
                                        "2021-01-25T18:30": 0.1,
                                        "2021-01-25T18:45": 0.1,
                                        "2021-01-25T19:00": 0.1,
                                        "2021-01-25T19:15": 0.1,
                                        "2021-01-25T19:30": 0.1,
                                        "2021-01-25T19:45": 0.1,
                                        "2021-01-25T20:00": 0.1,
                                        "2021-01-25T20:15": 0.1,
                                        "2021-01-25T20:30": 0.1,
                                        "2021-01-25T20:45": 0.1,
                                        "2021-01-25T21:00": 0.1,
                                        "2021-01-25T21:15": 0.1,
                                        "2021-01-25T21:30": 0.1,
                                        "2021-01-25T21:45": 0.1,
                                        "2021-01-25T22:00": 0.1,
                                        "2021-01-25T22:15": 0.1,
                                        "2021-01-25T22:30": 0.1,
                                        "2021-01-25T22:45": 0.1,
                                        "2021-01-25T23:00": 0.1,
                                        "2021-01-25T23:15": 0.1,
                                        "2021-01-25T23:30": 0.1,
                                        "2021-01-25T23:45": 0.1,
                                    },
                                }
                            ],
                        },
                        {
                            "name": "Home 3",
                            "tags": ["Home"],
                            "type": "Area",
                            "uuid": "mocked-uuid",
                            "geo_tag_location": (4.137182, 48.058159),
                            "address": "Berlin, Germany",
                            "children": [
                                {
                                    "name": "Load 3",
                                    "type": "Load",
                                    "uuid": "mocked-uuid",
                                    "geo_tag_location": (4.137182, 48.058159),
                                    "daily_load_profile": {
                                        "2021-01-25T00:00": 0.1,
                                        "2021-01-25T00:15": 0.1,
                                        "2021-01-25T00:30": 0.1,
                                        "2021-01-25T00:45": 0.1,
                                        "2021-01-25T01:00": 0.1,
                                        "2021-01-25T01:15": 0.1,
                                        "2021-01-25T01:30": 0.1,
                                        "2021-01-25T01:45": 0.1,
                                        "2021-01-25T02:00": 0.1,
                                        "2021-01-25T02:15": 0.1,
                                        "2021-01-25T02:30": 0.1,
                                        "2021-01-25T02:45": 0.1,
                                        "2021-01-25T03:00": 0.1,
                                        "2021-01-25T03:15": 0.1,
                                        "2021-01-25T03:30": 0.1,
                                        "2021-01-25T03:45": 0.1,
                                        "2021-01-25T04:00": 0.1,
                                        "2021-01-25T04:15": 0.1,
                                        "2021-01-25T04:30": 0.1,
                                        "2021-01-25T04:45": 0.1,
                                        "2021-01-25T05:00": 0.1,
                                        "2021-01-25T05:15": 0.1,
                                        "2021-01-25T05:30": 0.1,
                                        "2021-01-25T05:45": 0.1,
                                        "2021-01-25T06:00": 0.1,
                                        "2021-01-25T06:15": 0.1,
                                        "2021-01-25T06:30": 0.1,
                                        "2021-01-25T06:45": 0.1,
                                        "2021-01-25T07:00": 0.1,
                                        "2021-01-25T07:15": 0.1,
                                        "2021-01-25T07:30": 0.1,
                                        "2021-01-25T07:45": 0.1,
                                        "2021-01-25T08:00": 0.1,
                                        "2021-01-25T08:15": 0.1,
                                        "2021-01-25T08:30": 0.1,
                                        "2021-01-25T08:45": 0.1,
                                        "2021-01-25T09:00": 0.1,
                                        "2021-01-25T09:15": 0.1,
                                        "2021-01-25T09:30": 0.1,
                                        "2021-01-25T09:45": 0.1,
                                        "2021-01-25T10:00": 0.1,
                                        "2021-01-25T10:15": 0.1,
                                        "2021-01-25T10:30": 0.1,
                                        "2021-01-25T10:45": 0.1,
                                        "2021-01-25T11:00": 0.1,
                                        "2021-01-25T11:15": 0.1,
                                        "2021-01-25T11:30": 0.1,
                                        "2021-01-25T11:45": 0.1,
                                        "2021-01-25T12:00": 0.1,
                                        "2021-01-25T12:15": 0.1,
                                        "2021-01-25T12:30": 0.1,
                                        "2021-01-25T12:45": 0.1,
                                        "2021-01-25T13:00": 0.1,
                                        "2021-01-25T13:15": 0.1,
                                        "2021-01-25T13:30": 0.1,
                                        "2021-01-25T13:45": 0.1,
                                        "2021-01-25T14:00": 0.1,
                                        "2021-01-25T14:15": 0.1,
                                        "2021-01-25T14:30": 0.1,
                                        "2021-01-25T14:45": 0.1,
                                        "2021-01-25T15:00": 0.1,
                                        "2021-01-25T15:15": 0.1,
                                        "2021-01-25T15:30": 0.1,
                                        "2021-01-25T15:45": 0.1,
                                        "2021-01-25T16:00": 0.1,
                                        "2021-01-25T16:15": 0.1,
                                        "2021-01-25T16:30": 0.1,
                                        "2021-01-25T16:45": 0.1,
                                        "2021-01-25T17:00": 0.1,
                                        "2021-01-25T17:15": 0.1,
                                        "2021-01-25T17:30": 0.1,
                                        "2021-01-25T17:45": 0.1,
                                        "2021-01-25T18:00": 0.1,
                                        "2021-01-25T18:15": 0.1,
                                        "2021-01-25T18:30": 0.1,
                                        "2021-01-25T18:45": 0.1,
                                        "2021-01-25T19:00": 0.1,
                                        "2021-01-25T19:15": 0.1,
                                        "2021-01-25T19:30": 0.1,
                                        "2021-01-25T19:45": 0.1,
                                        "2021-01-25T20:00": 0.1,
                                        "2021-01-25T20:15": 0.1,
                                        "2021-01-25T20:30": 0.1,
                                        "2021-01-25T20:45": 0.1,
                                        "2021-01-25T21:00": 0.1,
                                        "2021-01-25T21:15": 0.1,
                                        "2021-01-25T21:30": 0.1,
                                        "2021-01-25T21:45": 0.1,
                                        "2021-01-25T22:00": 0.1,
                                        "2021-01-25T22:15": 0.1,
                                        "2021-01-25T22:30": 0.1,
                                        "2021-01-25T22:45": 0.1,
                                        "2021-01-25T23:00": 0.1,
                                        "2021-01-25T23:15": 0.1,
                                        "2021-01-25T23:30": 0.1,
                                        "2021-01-25T23:45": 0.1,
                                    },
                                }
                            ],
                        },
                    ],
                },
            ],
        }

        assert datasheet.global_coordinates == (4.137182, 48.058159)
        assert datasheet.settings.pop("start_date").format(DATE_TIME_FORMAT) == "2021-08-01T00:00"
        assert datasheet.settings.pop("end_date").format(DATE_TIME_FORMAT) == "2021-08-15T00:00"
        assert datasheet.settings == {
            "slot_length": timedelta(seconds=900),
            "currency": "EUR",
        }

        assert datasheet.advanced_settings == {
            "coefficient_algorithm": 1,
            "grid_fees_reduction": 0,
            "intracommunity_rate_base_eur": 0.3,
            "scm_cn_hours_of_delay": 0,
            "vat_percentage": 10,
            "self_consumption_type": 0,
            "enable_assistance_monthly_fee": False,
            "enable_contracted_power_cargo_monthly_fee": False,
            "enable_contracted_power_monthly_fee": False,
            "enable_energy_cargo_fee": False,
            "enable_grid_export_fee_const": False,
            "enable_grid_import_fee_const": False,
            "enable_marketplace_monthly_fee": False,
            "enable_electricity_tax": False,
            "enable_fixed_monthly_fee": False,
            "enable_service_monthly_fee": False,
            "enable_taxes_surcharges": False,
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
            "grid_import_fee_const": None,
            "taxes": None,
            "fixed_fee": None,
            "marketplace_fee": None,
            "assistance_fee": None,
            "coefficient_percent": None,
        }
        coordinates_builder = AssetCoordinatesBuilder()
        results = coordinates_builder.get_member_coordinates(member_information)

        location_converter_instance.convert.assert_called_with(
            "10210 La Loge-Pomblin, France 1234"
        )
        assert results == (12, 10)

    @staticmethod
    @patch(f"{BASE_MODULE}.LocationConverter", spec=True)
    def test_asset_coordinates_builder_raises_exceptions(location_converter_class_mock):
        """If instantiating the location converter causes an exception, it must be re-raised."""
        location_converter_class_mock.side_effect = LocationConverterException
        with pytest.raises(LocationConverterException):
            AssetCoordinatesBuilder()
