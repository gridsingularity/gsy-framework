"""Community Datasheet exceptions."""


class CommunityDatasheetException(Exception):
    """Exception raised while parsing the community datasheet."""


class StringToTimedeltaConversionException(Exception):
    """Exception raised when an error occurs while converting a string into timedelta."""
