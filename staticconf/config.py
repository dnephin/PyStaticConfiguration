"""
Singleton configuration object and value proxies.
"""
from staticconf import proxy, validation


__all__ = ['get', 'get_int', 'get_float', 'get_date', 'get_datetime']


value_proxies = []
configuration_values = {}


def register_proxy(proxy):
    value_proxy.append(proxy)


# TODO: reload config by resetting value on each value_proxy ?


def reset():
    """Used for internal testing."""
    value_proxies[:] = []
    configuration_values.clear()


def build_getter(validator):
    def proxy_register(name, default=proxy.UndefToken):
        args        = validator, configuration_values, name, default
        value_proxy = proxy.ValueProxy(*args)
        register_proxy(value_proxy)
        return value_proxy

    return proxy_register


get             = build_getter(validation.validate_string)
get_int         = build_getter(validation.validate_int)
get_float       = build_getter(validation.validate_float)
get_date        = build_getter(validation.validate_date)
get_datetime    = build_getter(validation.validate_datetime)
