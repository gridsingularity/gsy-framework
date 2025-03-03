from enum import Enum


class Stat(Enum):
    MIN = "min"
    MEDIAN = "median"
    MAX = "max"


ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"

CARBON_RATIO_G_KWH = "Ratio (gCO2eq/kWh)"

GENERATION_PLANT_TO_CARBON_EMISSIONS = {
    # source: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7
    # keys match the generation plants in the entsoe API
    # values in gCO2eq/kWh
    "Solar": {Stat.MIN: 18, Stat.MEDIAN: 48, Stat.MAX: 180},
    "Wind Onshore": {Stat.MIN: 7.0, Stat.MEDIAN: 11, Stat.MAX: 56},
    "Fossil Gas": {Stat.MIN: 410, Stat.MEDIAN: 490, Stat.MAX: 650},
    "Wind Offshore": {Stat.MIN: 8.0, Stat.MEDIAN: 12, Stat.MAX: 35},
    "Hydro Pumped Storage": {Stat.MIN: 1.0, Stat.MEDIAN: 24, Stat.MAX: 2200},
    "Nuclear": {Stat.MIN: 3.7, Stat.MEDIAN: 12, Stat.MAX: 110},
    "Biomass": {Stat.MIN: 620, Stat.MEDIAN: 740, Stat.MAX: 890},
    "Hydro Water Reservoir": {
        Stat.MIN: 1.0,
        Stat.MEDIAN: 24,
        Stat.MAX: 2200,
    },  # same as Hydro Pumped
    "Fossil Oil": {Stat.MIN: 410, Stat.MEDIAN: 490, Stat.MAX: 650},  # same as Fossil Gas
    "Fossil Oil shale": {
        Stat.MIN: 410,
        Stat.MEDIAN: 490,
        Stat.MAX: 650,
    },  # same as Fossil Oil due to lack of data
    "Hydro Run-of-river and poundage": {
        Stat.MIN: 1.0,
        Stat.MEDIAN: 24,
        Stat.MAX: 2200,
    },  # (same as Hydro Pumped),
    "Fossil Hard coal": {Stat.MIN: 740, Stat.MEDIAN: 820, Stat.MAX: 910},
    "Fossil Coal-derived gas": {
        Stat.MIN: 740,
        Stat.MEDIAN: 820,
        Stat.MAX: 910,
    },  # same as Fossil Gas
    "Fossil Brown coal/Lignite": {
        Stat.MIN: 740,
        Stat.MEDIAN: 820,
        Stat.MAX: 910,
    },  # same as Fossil Hard coal
    "Geothermal": {
        Stat.MIN: 6,
        Stat.MEDIAN: 38,
        Stat.MAX: 79,
    },  # Only lifecycle and no operation emissions
    "Other": {Stat.MIN: 50, Stat.MEDIAN: 300, Stat.MAX: 600},  # estimation
}


# see mappings https://github.com/EnergieID/entsoe-py/blob/master/entsoe/mappings.py
GEOPY_TO_ENTSOE_COUNTRY_CODE = {
    "AL": "AL",
    # "AD": "AD",
    "AT": "AT",
    "BY": "BY",
    "BE": "BE",
    "BA": "BA",
    "BG": "BG",
    "HR": "HR",
    "CY": "CY",
    "CZ": "CZ",
    "DK": "DK_CA",
    "EE": "EE",
    "FI": "FI",
    "FR": "FR",
    "DE": "DE_TRANSNET",
    "GR": "GR",
    "HU": "HU",
    "IS": "IS",
    "IE": "IE",
    "IT": "IT",
    "XK": "XK",
    "LV": "LV",
    # "LI": "LI",
    "LT": "LT",
    "LU": "LU",
    "MT": "MT",
    "MD": "MD",
    # "MC": "MC",
    "ME": "ME",
    "NL": "NL",
    "MK": "MK",
    "NO": "NO",
    "PL": "PL",
    "PT": "PT",
    "RO": "RO",
    # "SM": "SM",
    "RS": "RS",
    "SK": "SK",
    "SI": "SI",
    "ES": "ES",
    "SE": "SE",
    "CH": "CH",
    "UA": "UA",
    "GB": "GB",
    # "VA": "VA",
}

MONTHLY_CARBON_EMISSIONS_COUNTRY_CODES = [
    "AT",
    "AU-NSW",
    "BA",
    "BE",
    "BG",
    "BR",
    "CA-ON",
    "CH",
    "CL-SEN",
    "CR",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "ES",
    "FI",
    "FR",
    "GB-NIR",
    "GB",
    "GR",
    "HK",
    "HR",
    "HU",
    "ID",
    "IE",
    "IL",
    "IN-EA",
    "IS",
    "IT",
    "JP",
    "KR",
    "LT",
    "LU",
    "LV",
    "NI",
    "NL",
    "NO",
    "NZ",
    "PA",
    "PE",
    "PH",
    "PL",
    "PT",
    "RO",
    "RS",
    "SE",
    "SG",
    "SI",
    "SK",
    "TR",
    "TW",
    "US",
    "UY",
    "ZA",
]

YEARLY_CARBON_EMISSIONS_COUNTRY_CODES = [
    "AF",
    "DZ",
    "AS",
    "AO",
    "AG",
    "AR",
    "AM",
    "AW",
    "AU",
    "AZ",
    "BS",
    "BH",
    "BD",
    "BB",
    "BZ",
    "BJ",
    "BM",
    "BT",
    "BO",
    "BW",
    "BR",
    "VG",
    "BN",
    "BF",
    "BI",
    "KH",
    "CM",
    "CA",
    "CV",
    "KY",
    "CF",
    "TD",
    "CL",
    "CN",
    "CO",
    "KM",
    "CG",
    "CK",
    "CR",
    "CI",
    "CU",
    "CD",
    "DJ",
    "DM",
    "DO",
    "TL",
    "EC",
    "EG",
    "SV",
    "GQ",
    "ER",
    "SZ",
    "ET",
    "FK",
    "FO",
    "FJ",
    "GF",
    "PF",
    "GA",
    "GM",
    "GE",
    "GH",
    "GI",
    "GL",
    "GD",
    "GP",
    "GU",
    "GT",
    "GN",
    "GW",
    "GY",
    "HT",
    "HN",
    "HK",
    "IN",
    "ID",
    "IR",
    "IQ",
    "JM",
    "JP",
    "JO",
    "KZ",
    "KE",
    "KI",
]
