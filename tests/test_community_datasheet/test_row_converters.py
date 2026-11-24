from gsy_framework.community_datasheet.row_converters import MembersRowConverter

MEMBER_ARGS = {
    "email": "member@example.com",
    "member_uuid": "3f2b8c1e-6a4d-4e2b-9f1a-7c5d2e8b0a91",
    "zip_code": "10115",
    "address": "Street 1",
    "market_maker_rate": 30.0,
    "feed_in_tariff": 7.0,
    "coefficient_percentage": 0.0,
    "grid_import_fee_const": 0.0,
    "grid_export_fee_const": 0.0,
    "taxes_surcharges": 0.0,
    "electricity_tax": 0.0,
    "fixed_monthly_fee": 0.0,
    "marketplace_monthly_fee": 0.0,
    "assistance_monthly_fee": 0.0,
    "service_monthly_fee": 0.0,
    "contracted_power_monthly_fee": 0.0,
    "contracted_power_cargo_monthly_fee": 0.0,
    "energy_cargo_fee": 0.0,
    "geo_tag_location": [13.4, 52.5],  # given, so no geocoding request is made
}


class TestCreateMemberDict:

    @staticmethod
    def test_includes_the_did():
        did = "did:ethr:volta:0xf01b5c3dd6c97bf3583abb4cb99544b2b2ca34a6"

        member = MembersRowConverter.create_member_dict(**MEMBER_ARGS, did=did)

        assert member["did"] == did

    @staticmethod
    def test_did_defaults_to_none():
        assert MembersRowConverter.create_member_dict(**MEMBER_ARGS)["did"] is None
