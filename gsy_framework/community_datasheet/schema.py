"""Module containing schemas used to validate the community datasheet."""

COMMUNITY_DATASHEET_SCHEMA = {
    "type": "object",
    "properties": {
        "settings": {"$ref": "#/$defs/settings"},
        "grid": {"$ref": "#/$defs/grid"},
    },
    "$defs": {
        "settings": {
            "description": "General settings of the community.",
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "slot_length": {"type": "custom_timedelta"},
                "currency": {
                    "type": "string",
                    "enum": ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CNY", "CHF"]
                },
                "coefficient_type": {
                    "type": "string",
                    "enum": ["constant", "dynamic"]
                },
            },
            "required": ["start_date", "end_date", "slot_length", "currency", "coefficient_type"]
        },
        "grid": {"type": ["object"]}
    }
}
