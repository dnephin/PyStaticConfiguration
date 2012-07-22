"""
Validate and convert a configuration value to it's expected type.
"""
from staticconf.errors import ValidationError


def validate_string(value):
    return unicode(value)
        

def validate_int(value):
    try:
        return int(value)
    except ValueError:
        raise ValiationError("Invalid integer: %s" % value)


def validate_float(value):
    try:
        return float(value)
    except ValueError:
        raise ValidationError("Invalid float: %s" % value)


def validate_date(value):
    # TODO:
    pass


def validate_datetime(value):
    # TODO:
    pass


def no_validation(value):
    return value