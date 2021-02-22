"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


def is_load_node_type(area):
    return area['type'] in ["LoadHoursStrategy", "DefinedLoadStrategy",
                            "LoadHoursExternalStrategy", "LoadProfileExternalStrategy",
                            "LoadForecastExternalStrategy"]


def is_bulk_power_producer(area):
    return area['type'] in ["CommercialStrategy", "MarketMakerStrategy"]


def is_pv_node_type(area):
    return area['type'] in ["PVStrategy", "PVUserProfileStrategy", "PVPredefinedStrategy",
                            "PVExternalStrategy", "PVUserProfileExternalStrategy",
                            "PVPredefinedExternalStrategy", "PVForecastExternalStrategy"]


def is_finite_power_plant_node_type(area):
    return area['type'] == "FinitePowerPlant"


def is_producer_node_type(area):
    return is_bulk_power_producer(area) or is_pv_node_type(area) or \
           is_finite_power_plant_node_type(area)


def is_prosumer_node_type(area):
    return area['type'] in ["StorageStrategy", "StorageExternalStrategy"]


def is_buffer_node_type(area):
    return area['type'] == "InfiniteBusStrategy"


def get_unified_area_type(area):
    if is_pv_node_type(area):
        return "PV"
    elif is_load_node_type(area):
        return "Load"
    elif is_prosumer_node_type(area):
        return "Storage"
    elif is_bulk_power_producer(area) or is_buffer_node_type(area):
        return "MarketMaker"
    elif is_finite_power_plant_node_type(area):
        return "FinitePowerPlant"
    else:
        return "Area"


def area_sells_to_child(trade, area_name, child_names):
    return area_name_from_area_or_iaa_name(trade['seller']) == \
            area_name and area_name_from_area_or_iaa_name(trade['buyer']) in child_names


def child_buys_from_area(trade, area_name, child_names):
    return area_name_from_area_or_iaa_name(trade['buyer']) == \
        area_name and area_name_from_area_or_iaa_name(trade['seller']) in child_names


def area_name_from_area_or_iaa_name(name):
    return name[4:] if name[:4] == 'IAA ' else name


RESULT_NAMES_LIST = ["unmatched_loads", "price_energy_day", "cumulative_grid_trades", "bills", "cumulative_bills",
                     "device_statistics", "energy_trade_profile", "kpi", "area_throughput"]