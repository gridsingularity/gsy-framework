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
# flake8: noqa
import unittest
from jsonschema import ValidationError
from gsy_framework.results_validator import results_validator


class TestValidateResults(unittest.TestCase):

    def test_results_validator(self):

        results = {'job_id': '46ff19de-6a4d-4ce8-a6c9-cd7b2778f2fc',
                    "current_market": "2020-10-31T04:00",
                    'random_seed': 0,
                    'status': 'running',
                    'progress_info': {
                        "eta_seconds": 0,
                        "elapsed_time_seconds": 0,
                        "percentage_completed": 0
                    },
                   # TODO: remove `device_statistics`; It's only kept for backward compatibility.
                   "device_statistics": {},
                   "asset_statistics": {}
        }
        results_validator(results)

        results = {'job_id': '46ff19de-6a4d-4ce8-a6c9-cd7b2778f2fc',
                    "current_market": "2020-10-31T04:00",
                    'random_seed': 0,
                    'status': 'running',
                    'price_energy_day': {},
                    'cumulative_grid_trades': {},
                    'bills': {},
                    'cumulative_bills': {},
                    # TODO: remove `device_statistics`; It's only kept for backward compatibility.
                    'device_statistics': {},
                    'asset_statistics': {},
                    'energy_trade_profile': {}
                    }
        self.assertRaises(ValidationError, results_validator, results)

        results = { 'job_id': '46ff19de-6a4d-4ce8-a6c9-cd7b2778f2fc',
                    'random_seed': 0,
                    'price_energy_day': {},
                    'cumulative_grid_trades': {},
                    'bills': {},
                    'cumulative_bills': {},
                    'progress_info': {},
                    'status': 'running',
                    # TODO: remove `device_statistics`; It's only kept for backward compatibility.
                    'device_statistics': {},
                    'asset_statistics': {},
                    'not_a_parameter': {}
                    }
        self.assertRaises(ValidationError, results_validator, results)
