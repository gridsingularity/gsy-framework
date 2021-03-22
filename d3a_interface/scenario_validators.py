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

from jsonschema.validators import validate

from d3a_interface.constants_limits import ConstSettings
from d3a_interface.schemas import ScenarioSchemas


def scenario_validator(scenario_repr):
    validate(instance=scenario_repr, schema=ScenarioSchemas.scenario_schema)


def validate_area_name(area_dict: dict):
    area_name = area_dict.get('name', '')
    intersect = set(area_name).intersection(
        ConstSettings.GeneralSettings.AREA_NAME_RESTRICTED_CHARS)
    if intersect:
        raise ValueError('Area name cannot have special characters {intersect}.')