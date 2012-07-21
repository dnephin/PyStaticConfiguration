"""
Singleton configuration object and value proxies.
"""
from functools import partial
from staticconf import validation 


__all__ = [
    'get', 'get_int', 'get_float', 'get_date', 'get_datetime', 
    'ConfigurationError']


class ConfigurationError(ValueError):
    pass


class UnsetValueToken(object):
    pass


class ValueProxy(object):
    """Proxy a configuration value so it can be loaded after import time."""

    def __init__(self, validator, name, default=UnsetValueToken):
        self.validator  = validator
        self.name       = name
        self.default    = default
        self.value      = UnsetValueToken
        # Register this proxy
        value_proxies.append(self)

    def __getattr__(self, name):
        if self.value is not UnsetValueToken:
            return getattr(self.value, name)

        value = configuration_values.get(name, self.default)
        if value is UnsetValueToken:
            msg = "Configuration is missing value for: %s"
            raise ConfigurationError(msg % self.name)

        try:
            self.value = self.validator(value)
        except validation.ValidationError, e:
            msg = "Failed to validate %s: %s" % (self.name, e)
            raise ConfigurationError(msg)

        return getattr(self.value, name)


value_proxies = []
configuration_values = {}


def reset():
    """Used for internal testing."""
    value_proxies.clear()
    configuration_values.clear()


get         = partial(ValueProxy, validation.validate_string)
get_int     = partial(ValueProxy, validation.validate_int)
get_float   = partial(ValueProxy, validation.validate_float)
# TODO: the rest
