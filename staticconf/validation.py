"""
Validate and convert a configuration value to it's expected type.
"""

class ValidationError(ValueError):
    pass


def validate_string(value):
    return unicode(value)
        

def validate_int(value):
    try:
        return int(value)
    except ValueError:
        raise ValiationError("Invalid integer: %s" % value)


def validate_float(value):
    pass


def validate_date(value):
    pass


def validate_datetime(value):
    pass

