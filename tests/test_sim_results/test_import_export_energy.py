import uuid

from pendulum import now

from gsy_framework.sim_results.imported_exported_energy import ImportedExportedEnergyHandler


class TestImportedExportedEnergyHandler:
    # pylint: disable=attribute-defined-outside-init

    def setup_method(self):
        grid_uuid = str(uuid.uuid4())
        mm_name = "Infinite Bus"
        mm_uuid = str(uuid.uuid4())
        self.community_uuid = str(uuid.uuid4())
        self.house1_name = "House 1"
        self.house1_uuid = str(uuid.uuid4())
        self.house2_name = "House 2"
        self.house2_uuid = str(uuid.uuid4())

        self.area_dict = {
            "name": "Grid",
            "uuid": grid_uuid,
            "type": "Area",
            "children": [
                {"name": "InfiniteBus", "type": mm_name, "uuid": mm_uuid},
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
                        "seller": {"name": mm_name, "uuid": mm_uuid},
                        "buyer": {"name": self.house2_name, "uuid": self.house2_uuid},
                        "energy": 0.5,
                    },
                    {
                        "seller": {"name": self.house1_name, "uuid": self.house1_uuid},
                        "buyer": {"name": mm_name, "uuid": mm_uuid},
                        "energy": 0.6,
                    },
                ],
            }
        }

    def test_update_accumulates_trades_correctly_gsy_web(self):
        energy_handler = ImportedExportedEnergyHandler(False)
        energy_handler.update(self.area_dict, self.core_stats, now())

        assert energy_handler.imported_exported_energy == {
            self.house2_uuid: {
                "exported_to_community": 0.4,
                "imported_from_community": 0.3,
                "imported_from_grid": 0.5,
                "exported_to_grid": 0,
            },
            self.house1_uuid: {
                "exported_to_community": 0.3,
                "exported_to_grid": 0.6,
                "imported_from_community": 0.4,
                "imported_from_grid": 0,
            },
        }

    def test_update_accumulates_trades_correctly_gsy_e(self):
        energy_handler = ImportedExportedEnergyHandler(True)
        energy_handler.update(self.area_dict, self.core_stats, now())

        assert energy_handler.imported_exported_energy == {
            self.house2_name: {
                "exported_to_community": 0.4,
                "imported_from_community": 0.3,
                "imported_from_grid": 0.5,
                "exported_to_grid": 0,
            },
            self.house1_name: {
                "exported_to_community": 0.3,
                "exported_to_grid": 0.6,
                "imported_from_community": 0.4,
                "imported_from_grid": 0,
            },
        }
