from unittest.mock import MagicMock, patch

import pytest

from gsy_framework.community_datasheet.community_datasheet_parser import AssetCoordinatesBuilder
from gsy_framework.community_datasheet.location_converter import LocationConverterException

BASE_MODULE = "gsy_framework.community_datasheet.community_datasheet_parser"


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
