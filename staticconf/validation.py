"""
Validate and convert a configuration value to it's expected type.
"""
import datetime
import time
from staticconf.errors import ValidationError


def validate_string(value):
    return None if value is None else unicode(value)


def validate_bool(value):
    return None if value is None else bool(value)


def validate_numeric(type_func, value):
    try:
        return type_func(value)
    except ValueError:
        raise ValidationError("Invalid %s: %s" % (type_func.__name__, value))


def validate_int(value):
    return validate_numeric(int, value)


def validate_float(value):
    return validate_numeric(float, value)


date_formats = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %I:%M:%S %p",
    "%Y-%m-%d",
    "%y-%m-%d",
    "%m/%d/%y",
    "%m/%d/%Y",
]


def validate_datetime(value):
    if isinstance(value, datetime.datetime):
        return value

    for format in date_formats:
        try:
            return datetime.datetime.strptime(value, format)
        except ValueError:
            pass
    raise ValidationError("Invalid date format: %s" % value)


def validate_date(value):
    if isinstance(value, datetime.date):
        return value

    return validate_datetime(value).date()


time_formats = [
    "%I %p",
    "%H:%M",
    "%I:%M %p",
    "%H:%M:%S",
    "%I:%M:%S %p"
]


def validate_time(value):
    if isinstance(value, datetime.time):
        return value

    for format in time_formats:
        try:
            return datetime.time(*time.strptime(value, format)[3:6])
        except ValueError:
            pass
    raise ValidationError("Invalid time format: %s" % value)


def validate_iterable(iterable_type, value):
    """Convert the iterable to iterable_type, or raise a Configuration
    exception.
    """
    if isinstance(value, basestring):
        msg = "Invalid iterable of type(%s): %s"
        raise ValidationError(msg % (tuple(value), value))

    try:
        return iterable_type(value)
    except TypeError:
        raise ValidationError("Invalid iterable: %s" % (value))


def validate_list(value):
    return validate_iterable(list, value)


def validate_set(value):
    return validate_iterable(set, value)


def validate_tuple(value):
    return validate_iterable(tuple, value)


def validate_any(value):
    return value
