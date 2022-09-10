"""
Validate a configuration value by converting it to a specific type.

These functions are used by :mod:`staticconf.readers` and
:mod:`staticconf.schema` to coerce config values to a type.
"""
import datetime
import logging
import re
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import ItemsView
from typing import List
from typing import Optional
from typing import Pattern
from typing import Set
from typing import Tuple
from typing import TypeVar

from staticconf.errors import ValidationError


Validator = Callable[[Any], Any]
T = TypeVar("T")


def validate_string(value: Any) -> Optional[str]:
    return None if value is None else str(value)


def validate_bool(value: Any) -> Optional[bool]:
    return None if value is None else bool(value)


def validate_numeric(type_func: Callable[[Any], float], value: Any) -> float:
    try:
        return type_func(value)
    except ValueError:
        raise ValidationError(f"Invalid {type_func.__name__}: {value}")


def validate_int(value: Any) -> float:
    return validate_numeric(int, value)


def validate_float(value: Any) -> float:
    return validate_numeric(float, value)


date_formats = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %I:%M:%S %p",
    "%Y-%m-%d",
    "%y-%m-%d",
    "%m/%d/%y",
    "%m/%d/%Y",
]


def validate_datetime(value: Any) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        return value

    for format_ in date_formats:
        try:
            return datetime.datetime.strptime(value, format_)
        except ValueError:
            pass
    raise ValidationError(f"Invalid date format: {value}")


def validate_date(value: Any) -> datetime.date:
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


def validate_time(value: Any) -> datetime.time:
    if isinstance(value, datetime.time):
        return value

    for format_ in time_formats:
        try:
            return datetime.time(*time.strptime(value, format_)[3:6])
        except ValueError:
            pass
    raise ValidationError(f"Invalid time format: {value}")


def _validate_iterable(iterable_type: Callable[[Any], T], value: Any) -> T:
    """Convert the iterable to iterable_type, or raise a Configuration
    exception.
    """
    if isinstance(value, str):
        msg = "Invalid iterable of type(%s): %s"
        raise ValidationError(msg % (type(value), value))

    try:
        return iterable_type(value)
    except TypeError:
        raise ValidationError("Invalid iterable: %s" % (value))


def validate_list(value: Any) -> List[Any]:
    return _validate_iterable(list, value)


def validate_set(value: Any) -> Set[Any]:
    return _validate_iterable(set, value)


def validate_tuple(value: Any) -> Tuple[Any, ...]:
    return _validate_iterable(tuple, value)


def validate_regex(value: Any) -> Pattern[str]:
    try:
        return re.compile(value)
    except (re.error, TypeError) as e:
        raise ValidationError(f"Invalid regex: {e}, {value}")


def build_list_type_validator(
    item_validator: Validator
) -> Callable[[Any], List[Any]]:
    """Return a function which validates that the value is a list of items
    which are validated using item_validator.
    """
    def validate_list_of_type(value: Any) -> List[Any]:
        return [item_validator(item) for item in validate_list(value)]
    return validate_list_of_type


def build_map_type_validator(
    item_validator: Validator,
) -> Callable[[Any], Dict[Any, Any]]:
    """Return a function which validates that the value is a mapping of
    items. The function should return pairs of items that will be
    passed to the `dict` constructor.
    """
    def validate_mapping(value: Any) -> Dict[Any, Any]:
        return dict(item_validator(item) for item in validate_list(value))
    return validate_mapping


def validate_log_level(value: Any) -> int:
    """Validate a log level from a string value. Returns a constant from
    the :mod:`logging` module.
    """
    try:
        return getattr(logging, value)
    except AttributeError:
        raise ValidationError(f"Unknown log level: {value}")


def validate_any(value: Any) -> Any:
    return value


validators = {
    '':          validate_any,
    'bool':      validate_bool,
    'date':      validate_date,
    'datetime':  validate_datetime,
    'float':     validate_float,
    'int':       validate_int,
    'list':      validate_list,
    'set':       validate_set,
    'string':    validate_string,
    'time':      validate_time,
    'tuple':     validate_tuple,
    'regex':     validate_regex,
    'log_level': validate_log_level,
}


def get_validators() -> ItemsView[str, Validator]:
    """Return an iterator of (validator_name, validator) pairs."""
    return validators.items()
