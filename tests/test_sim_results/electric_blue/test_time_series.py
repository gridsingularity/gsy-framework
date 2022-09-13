import pytest
from pendulum import DateTime, duration

from gsy_framework.enums import AvailableMarketTypes
from gsy_framework.forward_markets.forward_profile import (
    ForwardTradeProfileGenerator)
from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.time_series import (
    ForwardDeviceTimeSeries, resample_data)


@pytest.fixture(name="device_stats")
def device_stats_fixture():
    """Return an object of type ForwardDeviceStats."""
    device_stats = ForwardDeviceStats(
        timeslot="2020-01-01T00:00:00",
        device_uuid="UUID_1",
        current_timeslot=DateTime(2020, 1, 1, 0, 0)
    )
    device_stats.add_trade({
        "seller_id": "UUID_1", "timeslot": "2020-01-01T00:00:00",
        "energy": 1, "price": 30})
    device_stats.add_trade({
        "seller_id": "UUID_2", "buyer_id": "UUID_1",
        "timeslot": "2020-01-01T00:00:00", "energy": 2, "price": 30})
    device_stats.add_offer({
        "seller_id": "UUID_1", "timeslot": "2020-01-01T00:00:00",
        "energy": 3, "price": 30})
    device_stats.add_bid({
        "buyer_id": "UUID_1", "timeslot": "2020-01-01T00:00:00",
        "energy": 4, "price": 30})

    return device_stats


class TestForwardDeviceTimeSeries:
    @staticmethod
    def test_generate(device_stats):
        time_series = ForwardDeviceTimeSeries(
            device_stats, AvailableMarketTypes.DAY_FORWARD
        )
        result = time_series.generate(resolution=duration(hours=12))

        assert result == {
            "matched_buy_orders_kWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 4.107887448076203,
                DateTime(2020, 1, 1, 12, 0, 0): 8.865222613298846},
            "matched_sell_orders_kWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 2.0539437240381013,
                DateTime(2020, 1, 1, 12, 0, 0): 4.432611306649423},
            "open_sell_orders_kWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 6.1618311721143035,
                DateTime(2020, 1, 1, 12, 0, 0): 13.297833919948268},
            "open_buy_orders_kWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 8.215774896152405,
                DateTime(2020, 1, 1, 12, 0, 0): 17.73044522659769},
            "all_buy_orders_KWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 12.323662344228607,
                DateTime(2020, 1, 1, 12, 0, 0): 26.595667839896535},
            "all_sell_orders_kWh": {
                DateTime(2020, 1, 1, 0, 0, 0): 8.215774896152405,
                DateTime(2020, 1, 1, 12, 0, 0): 17.73044522659769}
        }


def test_resampler():
    generator = ForwardTradeProfileGenerator(peak_kWh=2)
    profile = generator.generate_trade_profile(
        energy_kWh=2, market_slot=DateTime(2020, 1, 1, 0, 0, 0),
        product_type=AvailableMarketTypes.DAY_FORWARD)

    # duration of 12:30 hours is set on purpose to test if the resampler works correctly
    # when the profile duration is not dividable by aggregation time window.
    aggregated_data = resample_data(profile, duration(hours=12, minutes=30), aggregator_fn=sum)

    expected_result = {
        DateTime(2020, 1, 1, 0, 0, 0): sum(
            [profile[t] for t in filter(lambda x: x < DateTime(2020, 1, 1, 12, 30, 0), profile)]),
        DateTime(2020, 1, 1, 12, 30, 0): sum(
            [profile[t] for t in filter(lambda x: x >= DateTime(2020, 1, 1, 12, 30, 0), profile)])
    }

    assert aggregated_data == expected_result
