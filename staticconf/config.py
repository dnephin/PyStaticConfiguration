"""
Singleton configuration object and value proxies.
"""
import logging
import os
import time
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


class ConfigurationWatcher(object):
    """Watches a file for modification and reloads the configuration
    when it's modified.  Accepts a max_interval to throttle checks.
    """

    def __init__(self, config_loader, filename, max_interval=0, **kwargs):
        self.config_loader  = config_loader
        self.filename       = os.path.abspath(filename)
        self.max_interval   = max_interval
        self.loader_kwargs  = kwargs
        self.last_check     = time.time()
        self.last_modified  = os.path.getmtime(self.filename)

    @property
    def should_check(self):
        return self.last_check + self.max_interval <= time.time()

    def reload_if_changed(self, force=False):
        if (force or self.should_check) and self.file_modified():
            return self.reload()

    def file_modified(self):
        self.last_check     = time.time()
        prev_modified       = self.last_modified
        self.last_modified  = os.path.getmtime(self.filename)
        return prev_modified < self.last_modified

    def reload(self):
        config_dict = self.config_loader(self.filename, **self.loader_kwargs)
        reload()
        return config_dict