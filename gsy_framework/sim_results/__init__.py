"""
Copyright 2018 Grid Singularity
This file is part of Grid Singularity Exchange.

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
from gsy_framework.utils import area_name_from_area_or_ma_name


def is_load_node_type(area):
    """Check if the given asset is a load."""
    return area["type"] in ["LoadHoursStrategy", "DefinedLoadStrategy",
                            "LoadHoursExternalStrategy", "LoadProfileExternalStrategy",
                            "LoadForecastExternalStrategy", "Load"]


def is_bulk_power_producer(area):
    """Check if the given asset is a bulk power producer."""
    return area["type"] in ["CommercialStrategy", "MarketMakerStrategy"]


def is_pv_node_type(area):
    """Check if the given asset is a PV."""
    return area["type"] in ["PVStrategy", "PVUserProfileStrategy", "PVPredefinedStrategy",
                            "PVExternalStrategy", "PVUserProfileExternalStrategy",
                            "PVPredefinedExternalStrategy", "PVForecastExternalStrategy", "PV"]


def is_finite_power_plant_node_type(area):
    """Check if the given asset is a Finite Power Plant."""
    return area["type"] in ["FinitePowerPlant", "FiniteDieselGenerator"]


def is_producer_node_type(area):
    """Check if the given asset is a producer of any kind."""
    return (
        is_bulk_power_producer(area)
        or is_pv_node_type(area)
        or is_finite_power_plant_node_type(area))


def is_prosumer_node_type(area):
    """Check if the given asset is a prosumer."""
    return area["type"] in ["StorageStrategy", "StorageExternalStrategy", "Storage"]


def is_buffer_node_type(area):
    """Check if the given asset is an energy buffer."""
    return area["type"] == "InfiniteBusStrategy"


def get_unified_area_type(area):
    """Return the string that identifies the type of the given area."""
    if is_pv_node_type(area):
        return "PV"
    if is_load_node_type(area):
        return "Load"
    if is_prosumer_node_type(area):
        return "Storage"
    if is_bulk_power_producer(area) or is_buffer_node_type(area):
        return "MarketMaker"
    if is_finite_power_plant_node_type(area):
        return "FinitePowerPlant"

    return "Area"


def area_sells_to_child(trade, area_name, child_names):
    """Check if the area sold energy to one of its children (in the given trade)."""
    return (
        area_name_from_area_or_ma_name(trade["seller"]) == area_name
        and area_name_from_area_or_ma_name(trade["buyer"]) in child_names)


def child_buys_from_area(trade, area_name, child_names):
    """Check if the area bought energy from one of its children (in the given trade)."""
    return (
        area_name_from_area_or_ma_name(trade["buyer"]) == area_name
        and area_name_from_area_or_ma_name(trade["seller"]) in child_names)


def is_trade_external(trade, area_name, child_names):
    """Check if the given trade was conducted between the area and one if its children."""
    return (
        area_sells_to_child(trade, area_name, child_names)
        or child_buys_from_area(trade, area_name, child_names))
