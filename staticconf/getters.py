from staticconf import validation, config, proxy
from staticconf.proxy import UndefToken


__all__ = [
    'get',
    'get_bool',
    'get_date',
    'get_datetime',
    'get_float',
    'get_int',
    'get_string',
    'get_time',
    'NamespaceGetters'
]


def build_getter(validator, getter_namespace=None):
    """Create a getter function for retrieving values from the config cache.
    Getters will default to the DEFAULT namespace.
    """
    def proxy_register(key_name, default=UndefToken, help=None, namespace=None):
        name        = namespace or getter_namespace or config.DEFAULT
        namespace   = config.get_namespace(name)
        args        = validator, namespace.get_config_values(), key_name, default
        value_proxy = proxy.ValueProxy(*args)
        namespace.register_proxy(value_proxy)
        config.add_config_key_description(key_name, validator, default, name, help)
        return value_proxy

    return proxy_register


get             = build_getter(validation.validate_any)
get_bool        = build_getter(validation.validate_bool)
get_string      = build_getter(validation.validate_string)
get_int         = build_getter(validation.validate_int)
get_float       = build_getter(validation.validate_float)
get_date        = build_getter(validation.validate_date)
get_datetime    = build_getter(validation.validate_datetime)
get_time        = build_getter(validation.validate_time)
get_list        = build_getter(validation.validate_list)
get_set         = build_getter(validation.validate_set)
get_tuple       = build_getter(validation.validate_tuple)


class NamespaceGetters(object):
    """An object with getters, which have their namespace already defined."""

    def __init__(self, name):
        self.namespace      = name
        self.get            = build_getter(validation.validate_any, name)
        self.get_bool       = build_getter(validation.validate_bool, name)
        self.get_string     = build_getter(validation.validate_string, name)
        self.get_int        = build_getter(validation.validate_int, name)
        self.get_float      = build_getter(validation.validate_float, name)
        self.get_date       = build_getter(validation.validate_date, name)
        self.get_datetime   = build_getter(validation.validate_datetime, name)
        self.get_time       = build_getter(validation.validate_time, name)
        self.get_list       = build_getter(validation.validate_list, name)
        self.get_set        = build_getter(validation.validate_set, name)
        self.get_tuple      = build_getter(validation.validate_tuple, name)
