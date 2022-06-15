import uuid

from gsy_framework.sim_results.device_statistics import DeviceStatistics


class TestDeviceStatistics:
    # pylint: disable=(attribute-defined-outside-init
    def setup_method(self):
        self.area_uuid = str(uuid.uuid4())
        self.area_results_dict = {"name": "House", "type": "Area", "children": [
            {"name": "load", "type": "Load", "uuid": self.area_uuid}
            ]
        }
        self.core_stats = {
            "bids": [
                {"id": "2278f6e6-d634-41c9-8376-1300d68fd932", "time": "2021-06-30T19:30:30",
                 "type": "Bid", "buyer": "IAA Market", "energy": 9223372036854775807,
                 "buyer_id": "c1f1bdc6-816d-43de-9e66-12620acef969",
                 "energy_rate": 12.0, "buyer_origin": "Market Maker",
                 "buyer_origin_id": "c7f5429c-b9c3-4ca1-9966-24d61cdf1405",
                 "original_bid_price": 110680464442257310000},
                {"id": "19df3477-e294-4e92-ad77-b73329cb33ec", "time": "2021-06-30T19:30:30",
                 "type": "Bid", "buyer": "IAA Market", "energy": 0.125,
                 "buyer_id": "c1f1bdc6-816d-43de-9e66-12620acef969",
                 "energy_rate": 0.0, "buyer_origin": "TeslaPowerWall",
                 "buyer_origin_id": "cc6481e5-6af5-417f-9e35-8003a427cd57",
                 "original_bid_price": 0.0}],
            "offers": [
                {"id": "d54b2e7b-e2bc-4d82-a552-9d2492ff4604", "time": "2021-06-30T19:30:30",
                 "type": "Offer", "energy": 9223372036854775807, "seller": "IAA Market",
                 "seller_id": "c1f1bdc6-816d-43de-9e66-12620acef969", "energy_rate": 30.0,
                 "seller_origin": "Market Maker",
                 "seller_origin_id": "c7f5429c-b9c3-4ca1-9966-24d61cdf1405",
                 "original_offer_price": 276701161105643270000}],
            "trades": []}

    @staticmethod
    def test_update_returns_none_if_not_all_input_params_are_provided():

        assert DeviceStatistics(False).update() is None
        assert DeviceStatistics(False).update(area_result_dict={"some": "data"}) is None
        assert DeviceStatistics(False).update(core_stats={"some": "data"}) is None
        assert DeviceStatistics(False).update(current_market_slot="some_market_slot") is None
        assert DeviceStatistics(False).update(
            current_market_slot="some_market_slot",
            core_stats={"some": "data"}
        ) is None
        assert DeviceStatistics(False).update(
            area_result_dict={"some": "data"},
            core_stats={"some": "data"}
        ) is None

    def test_update_should_export_plots(self):
        DeviceStatistics(False).update(
            self.area_results_dict, self.core_stats, "2021-06-30T19:30:30")
