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

    def __init__(self, config_loader, filenames, max_interval=0):
        self.config_loader  = config_loader
        self.filenames      = self.get_filename_list(filenames)
        self.max_interval   = max_interval
        self.last_check     = time.time()

    def get_filename_list(self, filenames):
        if isinstance(filenames, basestring):
            filenames = [filenames]
        return [os.path.abspath(name) for name in filenames]

    @property
    def should_check(self):
        return self.last_check + self.max_interval <= time.time()

    @property
    def most_recent_changed(self):
        return max(os.path.getmtime(name) for name in self.filenames)

    def reload_if_changed(self, force=False):
        if (force or self.should_check) and self.file_modified():
            return self.reload()

    def file_modified(self):
        prev_check, self.last_check = self.last_check, time.time()
        return prev_check < self.most_recent_changed

    def reload(self):
        config_dict = self.config_loader()
        reload()
        return config_dict