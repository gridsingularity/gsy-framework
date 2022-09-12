import pytest
from pendulum import DateTime

from gsy_framework.sim_results.electric_blue.aggregate_results import \
    ForwardDeviceStats


@pytest.fixture(name="device_stats")
def device_stats_fixture():
    """Return an object of type ForwardDeviceStats."""
    return ForwardDeviceStats(
        timeslot="TIMESLOT_1",
        device_uuid="UUID_1",
        current_timeslot=DateTime(2020, 1, 1, 0, 0)
    )


class TestForwardDeviceStats:
    @staticmethod
    def test_add_sell_trade(device_stats):
        trade1 = {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 30}
        trade2 = {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        result = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 2,
            "total_energy_sold": 2,
            "total_earned_eur": 70,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0,
            "open_offers": [],
            "open_bids": [],
            "trades": [
                {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}]
        }
        assert device_stats.to_dict() == result

    @staticmethod
    def test_add_buy_trade(device_stats):
        trade1 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "timeslot": "TIMESLOT_1", "energy": 1, "price": 30}
        trade2 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        result = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 2,
            "total_energy_bought": 2,
            "total_spent_eur": 70,
            "open_offers": [],
            "open_bids": [],
            "trades": [
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}]
        }
        assert device_stats.to_dict() == result

    @staticmethod
    def test_add_buy_sell_trade(device_stats):
        trade1 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "timeslot": "TIMESLOT_1", "energy": 1, "price": 30}
        trade2 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}
        trade3 = {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                  "timeslot": "TIMESLOT_1", "energy": 2, "price": 40}
        trade4 = {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                  "timeslot": "TIMESLOT_1", "energy": 3, "price": 60}
        device_stats.add_trade(trade1)
        device_stats.add_trade(trade2)
        device_stats.add_trade(trade3)
        device_stats.add_trade(trade4)
        results = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 2,
            "total_energy_sold": 5,
            "total_earned_eur": 100,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 2,
            "total_energy_bought": 2,
            "total_spent_eur": 70,
            "open_offers": [],
            "open_bids": [],
            "trades": [
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 40},
                {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                 "timeslot": "TIMESLOT_1", "energy": 2, "price": 40},
                {"buyer_id": "UUID_2", "seller_id": "UUID_1",
                 "timeslot": "TIMESLOT_1", "energy": 3, "price": 60}]
        }
        assert device_stats.to_dict() == results

    @staticmethod
    def test_add_invalid_trade_raises_error(device_stats):
        trade = {"buyer_id": "UUID_2", "seller_id": "UUID_3",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 30}
        before_adding_trade = device_stats.to_dict()
        try:
            device_stats.add_trade(trade)
            pytest.fail("Device is not seller/buyer of the trade.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_trade

    @staticmethod
    def test_add_bid(device_stats):
        bid1 = {"buyer_id": "UUID_1", "price": 30, "energy": 1}
        bid2 = {"buyer_id": "UUID_1", "price": 60, "energy": 2}
        device_stats.add_bid(bid1)
        device_stats.add_bid(bid2)
        result = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0,
            "open_offers": [],
            "open_bids": [
                {"buyer_id": "UUID_1", "price": 30, "energy": 1},
                {"buyer_id": "UUID_1", "price": 60, "energy": 2}
            ],
            "trades": []
        }
        assert device_stats.to_dict() == result

    @staticmethod
    def test_add_invalid_bid_raises_error(device_stats):
        bid = {"buyer_id": "UUID_2", "price": 30, "energy": 1}
        before_adding_bid = device_stats.to_dict()
        try:
            device_stats.add_bid(bid)
            pytest.fail("Device is not buyer of the bid.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_bid

    @staticmethod
    def test_add_offer(device_stats):
        offer1 = {"seller_id": "UUID_1", "price": 30, "energy": 1}
        offer2 = {"seller_id": "UUID_1", "price": 60, "energy": 2}
        device_stats.add_offer(offer1)
        device_stats.add_offer(offer2)
        result = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 0,
            "total_energy_sold": 0,
            "total_earned_eur": 0,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 0,
            "total_energy_bought": 0,
            "total_spent_eur": 0,
            "open_offers": [
                {"seller_id": "UUID_1", "price": 30, "energy": 1},
                {"seller_id": "UUID_1", "price": 60, "energy": 2}],
            "open_bids": [],
            "trades": []
        }
        assert device_stats.to_dict() == result

    @staticmethod
    def test_add_invalid_offer_raises_error(device_stats):
        offer = {"seller_id": "UUID_2", "price": 30, "energy": 1}
        before_adding_offer = device_stats.to_dict()
        try:
            device_stats.add_offer(offer)
            pytest.fail("Device is not seller of the offer.")
        except AssertionError:
            pass
        assert device_stats.to_dict() == before_adding_offer

    @staticmethod
    def test_add_to_forward_device_stats(device_stats):
        global_device_stats_dict = {
            "timeslot": "TIMESLOT_1",
            "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 0, 0),
            "total_energy_produced": 0,
            "total_sell_trade_count": 1,
            "total_energy_sold": 1,
            "total_earned_eur": 30,
            "total_energy_consumed": 0,
            "total_buy_trade_count": 1,
            "total_energy_bought": 1,
            "total_spent_eur": 30,
            "open_offers": [{"seller_id": "UUID_1", "price": 30, "energy": 1}],
            "open_bids": [{"buyer_id": "UUID_1", "price": 30, "energy": 1}],
            "trades": [
                {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 30}]
        }
        global_device_stats = ForwardDeviceStats(**global_device_stats_dict)

        trade2 = {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}
        trade4 = {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                  "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}
        bid2 = {"buyer_id": "UUID_1", "price": 100, "energy": 2}
        offer2 = {"seller_id": "UUID_1", "price": 100, "energy": 2}

        device_stats.current_timeslot = DateTime(2020, 1, 1, 0, 15, 0)

        device_stats.add_trade(trade2)
        device_stats.add_trade(trade4)
        device_stats.add_bid(bid2)
        device_stats.add_offer(offer2)

        new_global_device_stats = global_device_stats + device_stats

        assert new_global_device_stats.to_dict() == {
            "timeslot": "TIMESLOT_1", "device_uuid": "UUID_1",
            "current_timeslot": DateTime(2020, 1, 1, 0, 15, 0),
            "total_energy_produced": 0, "total_sell_trade_count": 2,
            "total_energy_sold": 2, "total_earned_eur": 70,
            "total_energy_consumed": 0, "total_buy_trade_count": 2,
            "total_energy_bought": 2, "total_spent_eur": 70,
            "open_offers": [{"seller_id": "UUID_1", "price": 100, "energy": 2}],
            "open_bids": [{"buyer_id": "UUID_1", "price": 100, "energy": 2}],
            "trades": [
                {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 30},
                {"seller_id": "UUID_1", "timeslot": "TIMESLOT_1", "energy": 1, "price": 40},
                {"buyer_id": "UUID_1", "seller_id": "UUID_2",
                 "timeslot": "TIMESLOT_1", "energy": 1, "price": 40}]
        }
