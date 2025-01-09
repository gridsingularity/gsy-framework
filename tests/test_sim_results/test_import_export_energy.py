import uuid

import pytest
from pendulum import now

from gsy_framework.sim_results.imported_exported_energy import ImportedExportedEnergyHandler


class TestImportedExportedEnergyHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        grid_uuid = str(uuid.uuid4())
        self.community_uuid = str(uuid.uuid4())
        self.community_name = "Community"
        self.house1_name = "House 1"
        self.house1_uuid = str(uuid.uuid4())
        self.house2_name = "House 2"
        self.house2_uuid = str(uuid.uuid4())

        self.area_dict = {
            "name": "Grid",
            "uuid": grid_uuid,
            "type": "Area",
            "children": [
                {"name": "InfiniteBus", "type": "Infinite Bus", "uuid": str(uuid.uuid4())},
                {
                    "name": "Community",
                    "type": "Area",
                    "uuid": self.community_uuid,
                    "children": [
                        {
                            "name": self.house1_name,
                            "uuid": self.house1_uuid,
                            "type": "Area",
                            "children": [{"name": "PV", "type": "PV", "uuid": str(uuid.uuid4())}],
                        },
                        {
                            "name": self.house2_name,
                            "uuid": self.house2_uuid,
                            "type": "Area",
                            "children": [
                                {"name": "Load", "type": "Load", "uuid": str(uuid.uuid4())}
                            ],
                        },
                    ],
                },
            ],
        }
        self.core_stats = {
            self.community_uuid: {
                "trades": [
                    {
                        "seller": {"name": self.house1_name, "uuid": self.house1_uuid},
                        "buyer": {"name": self.house2_name, "uuid": self.house2_uuid},
                        "energy": 0.3,
                    },
                    {
                        "seller": {"name": self.house2_name, "uuid": self.house2_uuid},
                        "buyer": {"name": self.house1_name, "uuid": self.house1_uuid},
                        "energy": 0.4,
                    },
                    {
                        "seller": {"name": self.community_name, "uuid": self.community_uuid},
                        "buyer": {"name": self.house2_name, "uuid": self.house2_uuid},
                        "energy": 0.5,
                    },
                    {
                        "seller": {"name": self.house1_name, "uuid": self.house1_uuid},
                        "buyer": {"name": self.community_name, "uuid": self.community_uuid},
                        "energy": 0.6,
                    },
                ],
            }
        }

    @pytest.mark.parametrize("should_export_plots", [False, True])
    def test_update_accumulates_trades_correctly(self, should_export_plots):
        # Given
        energy_handler = ImportedExportedEnergyHandler(should_export_plots=should_export_plots)
        current_market_slot = now()

        # When
        energy_handler.update(self.area_dict, self.core_stats, current_market_slot)

        # Then
        member_1_key = self.house1_uuid if not should_export_plots else self.house1_name
        member_2_key = self.house2_uuid if not should_export_plots else self.house2_name
        member_1_accumulated_results = energy_handler.imported_exported_energy[member_1_key][
            "accumulated"
        ]
        member_2_accumulated_results = energy_handler.imported_exported_energy[member_2_key][
            "accumulated"
        ]
        member_1_slot_results = energy_handler.imported_exported_energy[member_1_key][
            current_market_slot
        ]
        member_2_slot_results = energy_handler.imported_exported_energy[member_2_key][
            current_market_slot
        ]
        member_1_expected_results = {
            "exported_to_community": 0.3,
            "exported_to_grid": 0.6,
            "imported_from_community": 0.4,
            "imported_from_grid": 0,
        }
        member_2_expected_results = {
            "exported_to_community": 0.4,
            "imported_from_community": 0.3,
            "imported_from_grid": 0.5,
            "exported_to_grid": 0,
        }
        assert member_1_accumulated_results == member_1_expected_results
        assert member_2_accumulated_results == member_2_expected_results
        assert member_1_slot_results == member_1_expected_results
        assert member_2_slot_results == member_2_expected_results
