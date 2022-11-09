import copy
import uuid
from unittest.mock import MagicMock, patch

import pytest
from pendulum import UTC, DateTime

from gsy_framework.sim_results.electric_blue.aggregate_results import (
    ForwardDeviceStats)
from gsy_framework.sim_results.electric_blue.all_results import (
    ForwardResultsHandler)
from gsy_framework.sim_results.electric_blue.time_series import (
    ForwardDeviceTimeSeries)
from gsy_framework.sim_results.electric_blue.utils import BaseStorage


@pytest.fixture(name="simulation_raw_data")
def simulation_raw_data_fixture():
    """Return a generator that produces simulation_raw_data
    which is part of the simulation market data message."""
    def func():
        for hour in range(1, 3):
            time_slot = f"2020-01-01T0{hour}:00:00"
            yield {"uuid_1234": {
                "forward_market_stats": {
                    4: {
                        time_slot:
                            {"bids": [
                                {"buyer_id": "UUID_1", "price": 30, "energy": 1,
                                 "time_slot": time_slot}],
                                "offers": [
                                    {"seller_id": "UUID_2", "price": 30, "energy": 1,
                                     "time_slot": time_slot}],
                                "trades": [
                                    {"seller_id": "UUID_2", "buyer_id": "UUID_1", "energy_rate": 1,
                                     "time_slot": time_slot, "energy": 1, "price": 30}],
                                "market_fee": 0.0}}}}}
    return func()


@pytest.fixture(name="results_handler")
def results_handler_fixture():
    """Return an object of type ForwardResultsHandler."""
    return ForwardResultsHandler(volume_time_series_storage=BaseStorage())


class TestForwardResultsHandler:

    @staticmethod
    def test_restore_asset_stats(results_handler):
        assert results_handler.previous_asset_stats == {}
        previous_stats = {4: {DateTime(2020, 1, 1, 0, 0, tzinfo=UTC): {uuid.uuid4(): MagicMock()}}}
        results_handler.restore_asset_stats(previous_stats)
        assert results_handler.previous_asset_stats == previous_stats

    @staticmethod
    def test_all_db_results(results_handler):
        orders = {uuid.uuid4(): {4: {DateTime(2020, 1, 1, 1, 0, tzinfo=UTC): {}}}}
        current_asset_stats = {4: {DateTime(2020, 1, 1, 1, 0, tzinfo=UTC): {uuid.uuid4(): None}}}
        time_series = {4: {1: {DateTime(2020, 1, 1, 1, 0, tzinfo=UTC): {uuid.uuid4(): {}}}}}
        results_handler.orders = orders
        results_handler.current_asset_stats = current_asset_stats
        results_handler.asset_time_series = time_series
        expected_results = {"orders": results_handler.orders,
                            "current_asset_stats": results_handler.current_asset_stats,
                            "asset_time_series": results_handler.asset_time_series,
                            "cumulative_net_energy_flow": {},
                            "cumulative_market_fees": 0.,
                            "asset_volume_time_series": results_handler.asset_volume_time_series}
        assert results_handler.all_db_results == expected_results

    @staticmethod
    def test_update(results_handler, simulation_raw_data):
        with patch.object(ForwardDeviceStats, "to_dict",
                          return_value="mocked-ForwardDeviceStats_dict"), \
            patch.object(ForwardDeviceTimeSeries, "generate",
                         return_value={}):
            assert results_handler.orders == {}
            assert results_handler.current_asset_stats == {}
            assert results_handler.asset_time_series == {}

            time_slot_dt = DateTime(2020, 1, 1, 1, 0, tzinfo=UTC)
            results_handler.update(
                {"children": [
                    {"uuid": "UUID_1", "capacity_kW": 1},
                    {"uuid": "UUID_2", "capacity_kW": 2}]},
                next(simulation_raw_data), "2020-01-01T00:00")

            assert results_handler.orders == ({
                'UUID_2': {
                    4: {
                        time_slot_dt: {
                            'offers': [{
                                'seller_id': 'UUID_2', 'price': 30, 'energy': 1,
                                'time_slot': '2020-01-01T01:00:00'}],
                            'bids': [],
                            'trades': [{
                                'seller_id': 'UUID_2', 'buyer_id': 'UUID_1', 'energy_rate': 1,
                                'time_slot': '2020-01-01T01:00:00', 'energy': 1,
                                'price': 30}]}}},
                'UUID_1': {
                    4: {
                        time_slot_dt:
                            {
                                'offers': [],
                                'bids': [{
                                    'buyer_id': 'UUID_1', 'price': 30, 'energy': 1,
                                    'time_slot': '2020-01-01T01:00:00'}],
                                'trades': [{
                                    'seller_id': 'UUID_2', 'buyer_id': 'UUID_1',
                                    'energy_rate': 1,
                                    'time_slot': '2020-01-01T01:00:00', 'energy': 1,
                                    'price': 30}]}}}})

            assert results_handler.current_asset_stats == {
                4: {
                    time_slot_dt: {
                        "UUID_2": "mocked-ForwardDeviceStats_dict",
                        "UUID_1": "mocked-ForwardDeviceStats_dict"}}}

            assert results_handler.asset_time_series == {
                4: {
                    0: {
                        time_slot_dt: {
                            "UUID_2": {},
                            "UUID_1": {}
                        }},
                    1: {
                        time_slot_dt: {
                            "UUID_2": {},
                            "UUID_1": {}
                        }}
                }}

    @staticmethod
    def test_results_handler_orders_consist_only_needed_attributes(results_handler,
                                                                   simulation_raw_data):
        needed_attributes = {"offers", "bids", "trades"}
        results_handler.update({
            "children": [
                {"uuid": "UUID_1", "capacity_kW": 1},
                {"uuid": "UUID_2", "capacity_kW": 2}]
        }, next(simulation_raw_data), "2020-01-01T00:00")
        orders = results_handler.orders["UUID_1"][4][DateTime(2020, 1, 1, 1, 0, tzinfo=UTC)]
        assert set(orders.keys()) == needed_attributes

    @staticmethod
    def test_if_previous_stats_are_buffered(results_handler, simulation_raw_data):
        results_handler.update({
            "children": [
                {"uuid": "UUID_1", "capacity_kW": 1},
                {"uuid": "UUID_2", "capacity_kW": 2}]
        }, next(simulation_raw_data), "2020-01-01T00:00")
        assert results_handler.previous_asset_stats == {}
        previous_asset_stats = copy.deepcopy(results_handler.current_asset_stats)
        results_handler.update({
            "children": [
                {"uuid": "UUID_1", "capacity_kW": 1},
                {"uuid": "UUID_2", "capacity_kW": 2}]
        }, next(simulation_raw_data), "2020-01-01T01:00")
        assert results_handler.previous_asset_stats == previous_asset_stats
