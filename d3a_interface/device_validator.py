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

import json
from d3a_interface.constants_limits import ConstSettings


GeneralSettings = ConstSettings.GeneralSettings
LoadSettings = ConstSettings.LoadSettings
PvSettings = ConstSettings.PVSettings

def validate(**kwargs):
    print(f"kwargs: {kwargs}")

    # LOAD VALIDATION
    if "avg_power_W" in kwargs and kwargs["avg_power_W"] is not None and \
            not LoadSettings.AVG_POWER_RANGE.min <= kwargs["avg_power_W"] <= LoadSettings.AVG_POWER_RANGE.max:
        return json.dumps({"mis_configuration": [f"avg_power_W should be in between "
                                                 f"{LoadSettings.AVG_POWER_RANGE.min} & "
                                                 f"{LoadSettings.AVG_POWER_RANGE.max}."]})
    # if (kwargs["avg_power_W"] is not None or kwargs["hrs_per_day"] is not None or
    #     kwargs["hrs_of_day"] is not None) and kwargs["daily_load_profile"] is not None:
    #     return json.dumps({"mis_configuration": [f"daily_load_profile shouldn't be set with"
    #                                              f"avg_power_W, hrs_per_day & hrs_of_day."]})
    # if kwargs["hrs_per_day"] is not None and \
    #         not LoadSettings.HOURS_RANGE.min <= kwargs["hrs_per_day"] <= LoadSettings.HOURS_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"hrs_per_day should be in between "
    #                                              f"{LoadSettings.HOURS_RANGE.min} & "
    #                                              f"{LoadSettings.HOURS_RANGE.max}."]})
    # if kwargs["final_buying_rate"] is not None and not \
    #         LoadSettings.FINAL_BUYING_RATE_RANGE.min <= kwargs["final_buying_rate"] <= LoadSettings.FINAL_BUYING_RATE_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"final_buying_rate should be in between "
    #                                              f"{LoadSettings.FINAL_BUYING_RATE_RANGE.min} & "
    #                                              f"{LoadSettings.FINAL_BUYING_RATE_RANGE.max}."]})
    # if kwargs["initial_buying_rate"] is not None and \
    #         not LoadSettings.INITIAL_BUYING_RATE_RANGE.min <= kwargs["initial_buying_rate"] <= \
    #             LoadSettings.INITIAL_BUYING_RATE_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"initial_buying_rate should be in between "
    #                                              f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.min} & "
    #                                              f"{LoadSettings.INITIAL_BUYING_RATE_RANGE.max}."]})
    # if kwargs["initial_buying_rate"] is not None and kwargs["final_buying_rate"] is not None and \
    #         kwargs["initial_buying_rate"] > kwargs["final_buying_rate"]:
    #     return json.dumps({"mis_configuration": [f"initial_buying_rate should be less than "
    #                                              f"final_buying_rate."]})
    # if kwargs["hrs_of_day"] is not None and \
    #         any([not LoadSettings.HOURS_RANGE.min <= h <= LoadSettings.HOURS_RANGE.max for h in kwargs["hrs_of_day"]]):
    #     return json.dumps({"mis_configuration": [f"hrs_of_day should be less between "
    #                                              f"{LoadSettings.HOURS_RANGE.min} & "
    #                                              f"{LoadSettings.HOURS_RANGE.max}."]})
    # if kwargs["hrs_of_day"] is not None and kwargs["hrs_per_day"] is not None and \
    #         len(kwargs["hrs_of_day"]) < kwargs["hrs_per_day"]:
    #     return json.dumps({"mis_configuration": [f"length of hrs_of_day list should be greater than hrs_per_day."]})
    # if kwargs["energy_rate_increase_per_update"] is not None and not \
    #         GeneralSettings.RATE_CHANGE_PER_UPDATE.min <= kwargs["energy_rate_increase_per_update"] <= \
    #         GeneralSettings.RATE_CHANGE_PER_UPDATE.max:
    #     return json.dumps({"mis_configuration": [f"energy_rate_increase_per_update should be in between "
    #                                              f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
    #                                              f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}."]})
    # if kwargs["fit_to_limit"] and kwargs["energy_rate_increase_per_update"] is not None:
    #     return json.dumps({"mis_configuration": [f"fit_to_limit & energy_rate_increase_per_update"
    #                                              f"can't be set together."]})
    #
    # # PV VALIDATION
    # if kwargs["panel_count"] is not None and not \
    #     PvSettings.PANEL_COUNT_RANGE.min <= kwargs["panel_count"] <= PvSettings.PANEL_COUNT_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"PV panel count should be in between "
    #                                              f"{PvSettings.PANEL_COUNT_RANGE.min} & "
    #                                              f"{PvSettings.PANEL_COUNT_RANGE.max}"]})
    # if kwargs["final_selling_rate"] is not None and \
    #     not PvSettings.MIN_SELL_RATE_RANGE.min <= kwargs["final_selling_rate"] <= PvSettings.MIN_SELL_RATE_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"final_selling_rate should be in between "
    #                                              f"{PvSettings.MIN_SELL_RATE_RANGE.min} & "
    #                                              f"{PvSettings.MIN_SELL_RATE_RANGE.max}"]})
    # if kwargs["initial_selling_rate"] is not None and not \
    #     PvSettings.INITIAL_RATE_RANGE.min <= kwargs["initial_selling_rate"] <= PvSettings.INITIAL_RATE_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"initial_selling_rate should be in between "
    #                                              f"{PvSettings.INITIAL_RATE_RANGE.min} & "
    #                                              f"{PvSettings.INITIAL_RATE_RANGE.max}"]})
    # if kwargs["initial_selling_rate"] is not None and kwargs["final_selling_rate"] is not None and \
    #     kwargs["initial_selling_rate"] < kwargs["final_selling_rate"]:
    #     return json.dumps({"mis_configuration": [f"initial_selling_rate should be greater"
    #                                              f"than or equal to final_selling_rate."]})
    # if kwargs["fit_to_limit"] is True and kwargs["energy_rate_decrease_per_update"] is not None:
    #     return json.dumps({"mis_configuration": [f"fit_to_limit & energy_rate_decrease_per_update"
    #                                              f"can't be set together."]})
    # if kwargs["energy_rate_decrease_per_update"] is not None and not \
    #     GeneralSettings.RATE_CHANGE_PER_UPDATE.min <= kwargs["energy_rate_decrease_per_update"] <= \
    #     GeneralSettings.RATE_CHANGE_PER_UPDATE.max:
    #     return json.dumps({"mis_configuration": [f"energy_rate_decrease_per_update should be in between "
    #                                              f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.min} & "
    #                                              f"{GeneralSettings.RATE_CHANGE_PER_UPDATE.max}"]})
    # if kwargs["max_panel_power_W"] is not None and \
    #         not PvSettings.MAX_PANEL_OUTPUT_W_RANGE.min <= kwargs["max_panel_power_W"] <= \
    #             PvSettings.MAX_PANEL_OUTPUT_W_RANGE.max:
    #     return json.dumps({"mis_configuration": [f"max_panel_power_W should be in between "
    #                                              f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.min} & "
    #                                              f"{PvSettings.MAX_PANEL_OUTPUT_W_RANGE.max}"]})
    # if kwargs["cloud_coverage"] is not None and kwargs["power_profile"] is not None:
    #     return json.dumps({"mis_configuration": [f"cloud_coverage & power_profile can't be "
    #                                              f"set together."]})

    return True
