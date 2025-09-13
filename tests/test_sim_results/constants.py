from pendulum import datetime

from gsy_framework.sim_results.carbon_emissions.constants import CARBON_RATIO_G_KWH

current_market_slot = datetime(2023, 1, 23, 15)

TEST_AREA_SETUP_PV_ONLY = {
    "name": "Grid",
    "children": [
        {
            "name": "House 2",
            "children": [
                {
                    "name": "H2 PV",
                    "uuid": "83c25853-4bdc-486d-9549-68178d6b7546",
                    "strategy": {
                        "type": "PVStrategy",
                        "kwargs": {
                            "panel_count": 1,
                            "capacity_kW": 1,
                            "fit_to_limit": True,
                            "update_interval": 60,
                            "initial_selling_rate": 80,
                            "final_selling_rate": 0,
                            "energy_rate_decrease_per_update": None,
                            "use_market_maker_rate": False,
                            "price_installation_per_kW": 100,
                        },
                    },
                    "display_type": "PVStrategy",
                },
            ],
            "uuid": "a8ff7ec0-3d15-4139-8801-ccea3cc3dd3f",
            "display_type": "Area",
        },
    ],
    "uuid": "5a53cc1d-121b-4ce1-8c09-ac8a689843b6",
    "display_type": "Area",
}

TEST_AREA_RESULTS_DICT = {
    "name": "Grid",
    "uuid": "70b818d1-491f-49ca-8566-1334eec06f15",
    "parent_uuid": "",
    "type": "Area",
    "children": [
        {
            "name": "House 2",
            "uuid": "394ee848-5c6b-4fe3-a035-223a38c855d1",
            "parent_uuid": "70b818d1-491f-49ca-8566-1334eec06f15",
            "type": "Area",
            "children": [
                {
                    "name": "H2 General Load",
                    "uuid": "6a849857-7c36-45f3-8712-5702006fe3fe",
                    "parent_uuid": "394ee848-5c6b-4fe3-a035-223a38c855d1",
                    "type": "LoadHoursStrategy",
                    "children": [],
                },
                {
                    "name": "H2 PV",
                    "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    "parent_uuid": "394ee848-5c6b-4fe3-a035-223a38c855d1",
                    "type": "PVStrategy",
                    "children": [],
                },
                {
                    "name": "H2 HeatPump",
                    "uuid": "8115e950-7422-4942-b4e5-237658404d80",
                    "parent_uuid": "394ee848-5c6b-4fe3-a035-223a38c855d1",
                    "type": "HeatPumpStrategy",
                    "children": [],
                },
            ],
        }
    ],
}


TEST_CORE_STATS = {
    "70b818d1-491f-49ca-8566-1334eec06f15": {
        "bids": [],
        "offers": [],
        "trades": [],
        "market_fee": 0,
        "const_fee_rate": 0.0,
        "feed_in_tariff": 20,
        "market_maker_rate": 30,
        "area_throughput": {
            "baseline_peak_energy_import_kWh": None,
            "baseline_peak_energy_export_kWh": None,
            "import_capacity_kWh": 0.0,
            "export_capacity_kWh": 0.0,
            "imported_energy_kWh": 0.0,
            "exported_energy_kWh": 0.0,
        },
        "grid_fee_constant": 0.0,
    },
    "394ee848-5c6b-4fe3-a035-223a38c855d1": {"bids": [], "offers": [], "trades": []},
    "6a849857-7c36-45f3-8712-5702006fe3fe": {
        "bids": [],
        "offers": [],
        "trades": [
            {
                "type": "Trade",
                "match_type": "Offer",
                "id": "3db38152-b44d-4038-aba6-b66e3a263690",
                "bid": None,
                "offer": {
                    "type": "Offer",
                    "id": "61308896-5fc5-4e67-9aa6-36b19b836e7f",
                    "energy": 0.2,
                    "energy_rate": 17.71186441,
                    "price": 3.5423728820000004,
                    "original_price": 3.5423728828828827,
                    "creation_time": "2023-01-25T15:30:00",
                    "time_slot": "2023-01-25T15:00:00",
                    "seller": {
                        "name": "H2 PV",
                        "origin": "H2 PV",
                        "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                        "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    },
                },
                "residual": {
                    "type": "Offer",
                    "id": "981c0fb7-df9a-4623-878a-b6f788fea15d",
                    "energy": 0.1108,
                    "energy_rate": 17.71186444,
                    "price": 1.96247458,
                    "original_price": 1.962474577117117,
                    "creation_time": "2023-01-25T15:30:00",
                    "time_slot": "2023-01-25T15:00:00",
                    "seller": {
                        "name": "H2 PV",
                        "origin": "H2 PV",
                        "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                        "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    },
                },
                "energy": 0.2,
                "energy_rate": 17.71186441,
                "price": 3.5423728820000004,
                "buyer": {
                    "name": "H2 General Load",
                    "origin": "H2 General Load",
                    "origin_uuid": "6a849857-7c36-45f3-8712-5702006fe3fe",
                    "uuid": "6a849857-7c36-45f3-8712-5702006fe3fe",
                },
                "seller": {
                    "name": "H2 PV",
                    "origin": "H2 PV",
                    "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                },
                "fee_price": 0.0,
                "creation_time": "2023-01-25T15:30:00",
                "time_slot": "2023-01-25T15:00:00",
                "offer_bid_trade_info": None,
            }
        ],
        "market_fee": 0.0,
        "load_profile_kWh": 0.2,
        "total_energy_demanded_wh": 800.0,
        "energy_requirement_kWh": 0.0,
    },
    "9f905a1f-b1aa-461f-9290-0be561932bf4": {
        "bids": [],
        "offers": [],
        "trades": [
            {
                "type": "Trade",
                "match_type": "Offer",
                "id": "3db38152-b44d-4038-aba6-b66e3a263690",
                "bid": None,
                "offer": {
                    "type": "Offer",
                    "id": "61308896-5fc5-4e67-9aa6-36b19b836e7f",
                    "energy": 0.2,
                    "energy_rate": 17.71186441,
                    "price": 3.5423728820000004,
                    "original_price": 3.5423728828828827,
                    "creation_time": "2023-01-25T15:30:00",
                    "time_slot": "2023-01-25T15:00:00",
                    "seller": {
                        "name": "H2 PV",
                        "origin": "H2 PV",
                        "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                        "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    },
                },
                "residual": {
                    "type": "Offer",
                    "id": "981c0fb7-df9a-4623-878a-b6f788fea15d",
                    "energy": 0.1108,
                    "energy_rate": 17.71186444,
                    "price": 1.96247458,
                    "original_price": 1.962474577117117,
                    "creation_time": "2023-01-25T15:30:00",
                    "time_slot": "2023-01-25T15:00:00",
                    "seller": {
                        "name": "H2 PV",
                        "origin": "H2 PV",
                        "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                        "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    },
                },
                "energy": 0.2,
                "energy_rate": 17.71186441,
                "price": 3.5423728820000004,
                "buyer": {
                    "name": "H2 General Load",
                    "origin": "H2 General Load",
                    "origin_uuid": "6a849857-7c36-45f3-8712-5702006fe3fe",
                    "uuid": "6a849857-7c36-45f3-8712-5702006fe3fe",
                },
                "seller": {
                    "name": "H2 PV",
                    "origin": "H2 PV",
                    "origin_uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                    "uuid": "9f905a1f-b1aa-461f-9290-0be561932bf4",
                },
                "fee_price": 0.0,
                "creation_time": "2023-01-25T15:30:00",
                "time_slot": "2023-01-25T15:00:00",
                "offer_bid_trade_info": None,
            }
        ],
        "market_fee": 0.0,
        "pv_production_kWh": 0.3108,
        "available_energy_kWh": 0.11080000000000001,
    },
    "8115e950-7422-4942-b4e5-237658404d80": {
        "bids": [],
        "offers": [],
        "trades": [],
        "market_fee": 0.0,
        "storage_temp_C": 65,
        "energy_consumption_kWh": 10,
        "available_energy_kWh": 0.11080000000000001,
    },
}

TEST_TRADE_PROFILE_RESULTS = {
    "January 01 2024, 00:00 h": 0.2,
    "January 01 2024, 01:00 h": 0.2,
    "January 01 2024, 02:00 h": 0.2,
    "January 01 2024, 03:00 h": 0.2,
    "January 01 2024, 04:00 h": 0.2,
    "January 01 2024, 05:00 h": 0.2,
    "January 01 2024, 06:00 h": 0.2,
    "January 01 2024, 07:00 h": 0.2,
    "January 01 2024, 17:00 h": 0.2,
    "January 01 2024, 18:00 h": 0.2,
    "January 01 2024, 19:00 h": 0.2,
    "January 01 2024, 20:00 h": 0.2,
    "January 01 2024, 21:00 h": 0.2,
    "January 01 2024, 22:00 h": 0.2,
}

TEST_IMPORTED_EXPORTED_ENERGY_RESULTS = {
    "House 1": {
        "2024-01-01T00:00:00": {
            "exported_to_community": 0.3,
            "exported_to_grid": 0.6,
            "imported_from_community": 0.4,
            "imported_from_grid": 0,
        },
    },
    "House 2": {
        "2024-01-01T00:00:00": {
            "exported_to_community": 0.4,
            "imported_from_community": 0.3,
            "imported_from_grid": 0.5,
            "exported_to_grid": 0,
        },
    },
}

TEST_CARBON_RATIO = [{"time": datetime(2024, 1, 1, 0, 0), CARBON_RATIO_G_KWH: 148.93}]
