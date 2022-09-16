import pytest
from pendulum import UTC, DateTime

from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats, handle_forward_results)


@pytest.fixture(name="device_stats")
def device_stats_fixture():
    """Return an object of type ForwardDeviceStats."""
    return ForwardDeviceStats(
        time_slot=DateTime(2020, 1, 1, 0, 0, tzinfo=UTC),
        device_uuid="UUID_1",
        current_time_slot=DateTime(2020, 1, 1, 0, 0, tzinfo=UTC)
    )


class TestForwardDeviceStats:
    @staticmethod
    def test_add_sell_trade(device_stats):
        trade1 = {
            "seller_id": "UUID_1", "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 30}
        trade2 = {
            "seller_id": "UUID_1", "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 40}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        result = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 2,
            "total_energy_sold": 2,
            "total_earned_eur": 70,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0,
        }
        assert device_stats.to_dict() == result

        assert device_stats.open_bids == []
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_buy_trade(device_stats):
        trade1 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 30}
        trade2 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 40}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        result = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 2,
            "total_energy_bought": 2,
            "total_spent_eur": 70
        }
        assert device_stats.to_dict() == result
        assert device_stats.open_bids == []
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_buy_sell_trade(device_stats):
        trade1 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 30}
        trade2 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 40}
        trade3 = {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                  "time_slot": "2020-01-01T00:00:00", "energy": 2, "price": 40}
        trade4 = {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                  "time_slot": "2020-01-01T00:00:00", "energy": 3, "price": 60}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        device_stats.add_trade(trade3)
        device_stats.add_trade(trade4)
        results = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 2,
            "total_energy_sold": 5,
            "total_earned_eur": 100,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 2,
            "total_energy_bought": 2,
            "total_spent_eur": 70,
        }
        assert device_stats.to_dict() == results
        assert device_stats.open_bids == []
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_invalid_trade_raises_error(device_stats):
        trade = {"buyer_id": "UUID_2", "seller_id": "UUID_3",
                 "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 30}
        before_adding_trade = device_stats.to_dict()
        try:
            device_stats.add_trade(trade)
            pytest.fail("Device is not seller/buyer of the trade.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_trade
        assert device_stats.open_bids == []
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_bid(device_stats):
        bid1 = {"buyer_id": "UUID_1", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"}
        bid2 = {"buyer_id": "UUID_1", "price": 60, "energy": 2, "time_slot": "2020-01-01T00:00:00"}
        device_stats.add_bid(bid1)
        device_stats.add_bid(bid2)
        result = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0,
        }
        assert device_stats.to_dict() == result
        assert device_stats.open_bids == [
            {"buyer_id": "UUID_1", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"},
            {"buyer_id": "UUID_1", "price": 60, "energy": 2, "time_slot": "2020-01-01T00:00:00"}
        ]
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_invalid_bid_raises_error(device_stats):
        bid = {"buyer_id": "UUID_2", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"}
        before_adding_bid = device_stats.to_dict()
        try:
            device_stats.add_bid(bid)
            pytest.fail("Device is not buyer of the bid.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_bid

    @staticmethod
    def test_add_offer(device_stats):
        offer1 = {"seller_id": "UUID_1", "price": 30, "energy": 1,
                  "time_slot": "2020-01-01T00:00:00"}
        offer2 = {"seller_id": "UUID_1", "price": 60, "energy": 2,
                  "time_slot": "2020-01-01T00:00:00"}
        device_stats.add_offer(offer1)
        device_stats.add_offer(offer2)
        result = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0
        }
        assert device_stats.to_dict() == result
        assert device_stats.open_bids == []
        assert device_stats.open_offers == [
            {"seller_id": "UUID_1", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"},
            {"seller_id": "UUID_1", "price": 60, "energy": 2, "time_slot": "2020-01-01T00:00:00"}
        ]

    @staticmethod
    def test_add_invalid_offer_raises_error(device_stats):
        offer = {"seller_id": "UUID_2", "price": 30, "energy": 1,
                 "time_slot": "2020-01-01T00:00:00"}
        before_adding_offer = device_stats.to_dict()
        try:
            device_stats.add_offer(offer)
            pytest.fail("Device is not seller of the offer.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_offer
        assert device_stats.open_bids == []
        assert device_stats.open_offers == []

    @staticmethod
    def test_add_to_forward_device_stats(device_stats):
        global_device_stats_dict = {
            "time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            "total_energy_produced": 0,
            "total_sell_trade_count": 1,
            "total_energy_sold": 1,
            "total_earned_eur": 30,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 1,
            "total_energy_bought": 1,
            "total_spent_eur": 30,
        }
        global_device_stats = ForwardDeviceStats(**global_device_stats_dict)

        trade2 = {"seller_id": "UUID_1", "time_slot": "2020-01-01T00:00:00",
                  "energy": 1, "price": 40}
        trade4 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "time_slot": "2020-01-01T00:00:00", "energy": 1, "price": 40}
        bid1 = {"buyer_id": "UUID_1", "price": 100, "energy": 2,
                "time_slot": "2020-01-01T00:00:00"}
        offer1 = {"seller_id": "UUID_1", "price": 100, "energy": 2,
                  "time_slot": "2020-01-01T00:00:00"}
        bid2 = {"buyer_id": "UUID_1", "price": 30, "energy": 1,
                "time_slot": "2020-01-01T00:00:00"}
        offer2 = {"seller_id": "UUID_1", "price": 30, "energy": 1,
                  "time_slot": "2020-01-01T00:00:00"}

        device_stats.current_time_slot = DateTime(2020, 1, 1, 0, 15, 0, tzinfo=UTC)

        device_stats.add_trade(trade2)
        device_stats.add_trade(trade4)
        device_stats.add_bid(bid1)
        device_stats.add_offer(offer1)

        new_global_device_stats = global_device_stats + device_stats

        new_global_device_stats.add_bid(bid2)
        new_global_device_stats.add_offer(offer2)

        assert new_global_device_stats.to_dict() == {
            "time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC), "device_uuid": "UUID_1",
            "current_time_slot": DateTime(2020, 1, 1, 0, 15, 0, tzinfo=UTC),
            "total_energy_produced": 0, "total_sell_trade_count": 2,
            "total_energy_sold": 2, "total_earned_eur": 70,
            "total_energy_consumed": 0, "total_buy_trade_count": 2,
            "total_energy_bought": 2, "total_spent_eur": 70,
        }
        assert new_global_device_stats.open_bids == [
            {"buyer_id": "UUID_1", "price": 100, "energy": 2, "time_slot": "2020-01-01T00:00:00"},
            {"buyer_id": "UUID_1", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"}
        ]
        assert new_global_device_stats.open_offers == [
            {"seller_id": "UUID_1", "price": 100, "energy": 2, "time_slot": "2020-01-01T00:00:00"},
            {"seller_id": "UUID_1", "price": 30, "energy": 1, "time_slot": "2020-01-01T00:00:00"}
        ]

    @staticmethod
    def test_invalid_time_slot_raises_error(device_stats):
        trade = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "time_slot": "2020-01-02T00:00:00", "energy": 1, "price": 40}
        bid = {"buyer_id": "UUID_1", "price": 100, "energy": 2, "time_slot": "2020-01-02T00:00:00"}
        offer = {"seller_id": "UUID_1", "price": 100, "energy": 2,
                 "time_slot": "2020-01-02T00:00:00"}
        try:
            device_stats.add_trade(trade)
            pytest.fail("Invalid time_slot got accepted.")
        except AssertionError:
            pass
        try:
            device_stats.add_bid(bid)
            pytest.fail("Invalid time_slot got accepted.")
        except AssertionError:
            pass
        try:
            device_stats.add_offer(offer)
            pytest.fail("Invalid time_slot got accepted.")
        except AssertionError:
            pass

        assert device_stats.open_bids == []
        assert device_stats.open_offers == []


class TestForwardResultsHandler:
    @staticmethod
    def test_handle_forward_results():
        current_time_slot = DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
        market_stats = {
            "2020-02-01T00:00:00": {
                "bids": [{"buyer_id": "UUID_2", "time_slot": "2020-02-01T00:00:00"}],
                "offers": [{"seller_id": "UUID_1", "time_slot": "2020-02-01T00:00:00"}],
                "trades": [{
                    "seller_id": "UUID_1", "buyer_id": "UUID_2", "energy": 1,
                    "price": 30, "time_slot": "2020-02-01T00:00:00"}]
            },
            "2020-03-01T00:00:00": {
                "bids": [{"buyer_id": "UUID_4", "time_slot": "2020-03-01T00:00:00"}],
                "offers": [{"seller_id": "UUID_3", "time_slot": "2020-03-01T00:00:00"}],
                "trades": [{
                    "seller_id": "UUID_3", "buyer_id": "UUID_4", "energy": 2,
                    "price": 40, "time_slot": "2020-03-01T00:00:00"}]
            },
        }
        result = dict(handle_forward_results(current_time_slot, market_stats))
        for time_slot in result:
            for device_uuid in result[time_slot]:
                result[time_slot][device_uuid] = result[time_slot][device_uuid].to_dict()

        expected_result = {
            DateTime(2020, 2, 1, 0, 0, tzinfo=UTC): {
                "UUID_1": {
                    "time_slot": DateTime(2020, 2, 1, 0, 0, tzinfo=UTC), "device_uuid": "UUID_1",
                    "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
                    "total_energy_produced": 0, "total_sell_trade_count": 1,
                    "total_energy_sold": 1, "total_earned_eur": 30, "total_energy_consumed": 0,
                    "total_buy_trade_count": 0, "total_energy_bought": 0, "total_spent_eur": 0,
                },
                "UUID_2": {
                    "time_slot": DateTime(2020, 2, 1, 0, 0, tzinfo=UTC), "device_uuid": "UUID_2",
                    "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
                    "total_energy_produced": 0, "total_sell_trade_count": 0,
                    "total_energy_sold": 0, "total_earned_eur": 0, "total_energy_consumed": 0,
                    "total_buy_trade_count": 1, "total_energy_bought": 1, "total_spent_eur": 30,
                }
            },
            DateTime(2020, 3, 1, 0, 0, tzinfo=UTC): {
                "UUID_3": {
                    "time_slot": DateTime(2020, 3, 1, 0, 0, tzinfo=UTC), "device_uuid": "UUID_3",
                    "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
                    "total_energy_produced": 0, "total_sell_trade_count": 1,
                    "total_energy_sold": 2, "total_earned_eur": 40, "total_energy_consumed": 0,
                    "total_buy_trade_count": 0, "total_energy_bought": 0, "total_spent_eur": 0,
                },
                "UUID_4": {
                    "time_slot": DateTime(2020, 3, 1, 0, 0, tzinfo=UTC), "device_uuid": "UUID_4",
                    "current_time_slot": DateTime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
                    "total_energy_produced": 0, "total_sell_trade_count": 0,
                    "total_energy_sold": 0, "total_earned_eur": 0, "total_energy_consumed": 0,
                    "total_buy_trade_count": 1, "total_energy_bought": 2, "total_spent_eur": 40,
                }
            },
        }
        assert result == expected_result
