from uuid import uuid4

import pytest

from gsy_framework.sim_results.kpi import KPI, SavingsKPI
from gsy_framework.constants_limits import GlobalConfig


class FakeEndpointBuffer:
    grid_uuid = str(uuid4())
    house1_uuid = str(uuid4())
    house2_uuid = str(uuid4())
    pv_uuid = str(uuid4())
    load_uuid = str(uuid4())
    pv2_uuid = str(uuid4())
    endpoint_dict = {}
    area_dict = {
        "name": "grid", "uuid": grid_uuid, "parent_uuid": "", "children": [
            {
                "name": "house1", "type": "Area", "uuid": house1_uuid, "parent_uuid": grid_uuid,
                "children": [
                    {
                        "name": "pv", "type": "PVStrategy", "uuid": pv_uuid,
                        "parent_uuid": house1_uuid, "children": []},
                    {
                        "name": "load", "type": "LoadHoursStrategy", "uuid": load_uuid,
                        "parent_uuid": house1_uuid, "children": []}
                ]},
            {
                "name": "house2", "type": "Area", "uuid": house2_uuid, "parent_uuid": grid_uuid,
                "children": [
                    {
                        "name": "pv2", "type": "PVStrategy", "uuid": pv2_uuid,
                        "parent_uuid": house2_uuid, "children": []},
                ]}
        ]}
    core_stats = {
        grid_uuid: {"const_fee_rate": 1, "feed_in_tariff": 20.0, "market_maker_rate": 30.0},
        house1_uuid: {"const_fee_rate": 0.5, "feed_in_tariff": 20.0, "market_maker_rate": 30.0}
    }
    current_market_slot = "2021-09-13T12:45"


@pytest.fixture
def savings_kpi():
    return SavingsKPI()


@pytest.fixture
def kpi():
    return KPI()


def test_populate_consumer_producer_sets_are_correct(savings_kpi):
    pv_uuid = str(uuid4())
    load_uuid = str(uuid4())
    ess_uuid = str(uuid4())
    test_area = {
         "name": "house",
         "children": [
             {"name": "pv1", "uuid": pv_uuid, "type": "PV", "panel_count": 4},
             {"name": "load1", "uuid": load_uuid, "type": "LoadHoursStrategy",
              "avg_power_W": 200},
             {"name": "storage1", "uuid": ess_uuid, "type": "StorageExternalStrategy"}
         ]
       }
    savings_kpi.populate_consumer_producer_sets(test_area)
    assert savings_kpi.producer_ess_set == {pv_uuid, ess_uuid}
    assert savings_kpi.consumer_ess_set == {load_uuid, ess_uuid}


def test_root_to_target_area_grid_fee_accumulation(kpi):
    endpoint_buffer = FakeEndpointBuffer()

    kpi.update(endpoint_buffer.area_dict,
               endpoint_buffer.core_stats,
               endpoint_buffer.current_market_slot)
    assert kpi.area_uuid_cum_grid_fee_mapping[endpoint_buffer.grid_uuid] == 1.0
    assert kpi.area_uuid_cum_grid_fee_mapping[endpoint_buffer.house1_uuid] == 1.5
    assert kpi.area_uuid_cum_grid_fee_mapping[endpoint_buffer.house2_uuid] == 1.0


def test_get_feed_in_tariff_rate_excluding_path_grid_fees(kpi, savings_kpi):
    endpoint_buffer = FakeEndpointBuffer()
    kpi.update(endpoint_buffer.area_dict, endpoint_buffer.core_stats,
               endpoint_buffer.current_market_slot)
    house1_core_stats = endpoint_buffer.core_stats.get(endpoint_buffer.house1_uuid, {})

    expected_fit_minus_glp = savings_kpi.get_feed_in_tariff_rate_excluding_path_grid_fees(
        house1_core_stats,
        kpi.area_uuid_cum_grid_fee_mapping[endpoint_buffer.house1_uuid])

    actual_fit_minus_glp = GlobalConfig.FEED_IN_TARIFF - (
            endpoint_buffer.core_stats[endpoint_buffer.grid_uuid]["const_fee_rate"] +
            endpoint_buffer.core_stats[endpoint_buffer.house1_uuid]["const_fee_rate"])

    assert actual_fit_minus_glp == expected_fit_minus_glp


def test_market_maker_rate_including_path_grid_fees(kpi, savings_kpi):
    endpoint_buffer = FakeEndpointBuffer()
    kpi.update(endpoint_buffer.area_dict, endpoint_buffer.core_stats,
               endpoint_buffer.current_market_slot)
    house1_core_stats = endpoint_buffer.core_stats.get(endpoint_buffer.house1_uuid, {})

    expected_mmr_minus_glp = savings_kpi.get_market_maker_rate_including_path_grid_fees(
        house1_core_stats,
        kpi.area_uuid_cum_grid_fee_mapping[endpoint_buffer.house1_uuid])

    actual_mmr_minus_glp = GlobalConfig.market_maker_rate + (
            endpoint_buffer.core_stats[endpoint_buffer.grid_uuid]["const_fee_rate"] +
            endpoint_buffer.core_stats[endpoint_buffer.house1_uuid]["const_fee_rate"])

    assert actual_mmr_minus_glp == expected_mmr_minus_glp
