"""
Singleton configuration object and value proxies.
"""
import logging
from staticconf import proxy, errors

log = logging.getLogger(__name__)

value_proxies = []
configuration_values = {}


def register_proxy(proxy):
    value_proxies.append(proxy)


def reload():
    for value_proxy in value_proxies:
        value_proxy.reset()


def set_configuration(config_data):
    configuration_values.update(config_data)


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


def validate_keys(keys, error_on_unknown):
    """Raise an exception if error_on_unknown is true, and keys contains
    a key which is not defined in a registeredValueProxy.
    """
    known_keys = set(proxy.config_key for proxy in value_proxies)
    unknown_keys = set(keys) - known_keys
    if not unknown_keys:
        return

    msg = "Unexpected keys in configuration: %s" % ', '.join(unknown_keys)
    if not error_on_unknown:
        log.warn(msg)
        return
    raise errors.ConfigurationError(msg)