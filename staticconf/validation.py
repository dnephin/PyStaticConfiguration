"""
Validate and convert a configuration value to it's expected type.
"""
import datetime
import time
from staticconf.errors import ValidationError


def validate_string(value):
    return unicode(value)

def validate_bool(value):
    return bool(value)

def validate_int(value):
    try:
        return int(value)
    except ValueError:
        raise ValidationError("Invalid integer: %s" % value)


def validate_float(value):
    try:
        return float(value)
    except ValueError:
        raise ValidationError("Invalid float: %s" % value)


date_formats = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %I:%M:%S %p",
    "%Y-%m-%d",
    "%y-%m-%d",
    "%m/%d/%y",
    "%m/%d/%Y",
]


def validate_datetime(value):
    for format in date_formats:
        try:
            return datetime.datetime.strptime(value, format)
        except ValueError:
            pass
    raise ValidationError("Invalid date format: %s" % value)


def validate_date(value):
    return validate_datetime(value).date()


time_formats = [
    "%H:%M:%S",
    "%I:%M:%S %p"
]

def validate_time(value):
    for format in time_formats:
        try:
            return datetime.time(*time.strptime(value, format)[3:6])
        except ValueError:
            pass
    raise ValidationError("Invalid time format: %s" % value)