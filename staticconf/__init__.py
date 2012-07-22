from staticconf import config, validation
from staticconf.loader import *


get             = config.build_getter(lambda v: v)
get_bool        = config.build_getter(validation.validate_bool)
get_string      = config.build_getter(validation.validate_string)
get_int         = config.build_getter(validation.validate_int)
get_float       = config.build_getter(validation.validate_float)
get_date        = config.build_getter(validation.validate_date)
get_datetime    = config.build_getter(validation.validate_datetime)
get_time        = config.build_getter(validation.validate_time)
