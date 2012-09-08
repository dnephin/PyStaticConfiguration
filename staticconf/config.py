"""
Static configuration.
"""
import logging
import os
import time
from collections import namedtuple
from staticconf import proxy, errors
from staticconf.proxy import UndefToken

log = logging.getLogger(__name__)


# Name for the default namespace
DEFAULT = 'default'


class ConfigNamespace(object):
    """A configuration namespace, which contains the list of value proxies
    and configuration values.
    """

    def __init__(self, name):
        self.name = name
        self.configuration_values = {}
        self.value_proxies = []

    def get_value_proxies(self):
        return self.value_proxies

    def register_proxy(self, proxy):
        """Register a new value proxy in this namespace."""
        self.value_proxies.append(proxy)

    def update_values(self, *args, **kwargs):
        self.configuration_values.update(*args, **kwargs)

    def get_config_values(self):
        return self.configuration_values

    def validate_keys(self, keys, error_on_unknown):
        """Raise an exception if error_on_unknown is true, and keys contains
        a key which is not defined in a registeredValueProxy.
        """
        known_keys = set(vproxy.config_key for vproxy in self.value_proxies)
        unknown_keys = set(keys) - known_keys
        if not unknown_keys:
            return

        msg = "Unexpected keys in configuration: %s" % ', '.join(unknown_keys)
        if not error_on_unknown:
            log.warn(msg)
            return
        raise errors.ConfigurationError(msg)

    def has_duplicate_keys(self, config_data, error_on_duplicate):
        args = config_data, self.configuration_values, error_on_duplicate
        return has_duplicate_keys(*args)

    def __getitem__(self, item):
        return self.configuration_values[item]

    def __setitem__(self, key, value):
        self.configuration_values[key] = value

    def __contains__(self, item):
        return item in self.configuration_values

    def _reset(self):
        self.configuration_values.clear()
        self.value_proxies[:] = []


config_key_descriptions = []
configuration_namespaces = {DEFAULT: ConfigNamespace(DEFAULT)}


KeyDescription = namedtuple('KeyDescription',
        'name validator default namespace help')


def get_namespace(name):
    """Retrieve a ConfigurationNamespace by name, creating the namespace if it
    does not exist.
    """
    if name not in configuration_namespaces:
        configuration_namespaces[name] = ConfigNamespace(name)
    return configuration_namespaces[name]


def reload(name=DEFAULT, all_names=False):
    """Reload one or more namespaces. Defaults to just the DEFAULT namespace.
    if all_names is True, reload all namespaces.
    """
    names = configuration_namespaces.keys() if all_names else [name]
    for name in names:
        namespace = get_namespace(name)
        for value_proxy in namespace.get_value_proxies():
            value_proxy.reset()


def add_config_key_description(name, validator, default, namespace, help):
    desc = KeyDescription(name, validator, default, namespace, help)
    config_key_descriptions.append(desc)


def validate(name=DEFAULT, all_names=False):
    """Access values in all registered proxies in a namespace. Missing values
    raise ConfigurationError. Defaults to the DEFAULT namespace. If all_names
     is True, validate all namespaces.
    """
    names = configuration_namespaces.keys() if all_names else [name]
    for name in names:
        namespace = get_namespace(name)
        all(bool(value_proxy) for value_proxy in namespace.get_value_proxies())


def view_help():
    """Return a help message describing all the statically configured keys.
    """
    def format(desc):
        help        = desc.help or ''
        default     = '' if desc.default is proxy.UndefToken else desc.default
        type_name   = desc.validator.__name__.replace('validate_', '')
        namespace   = '' if desc.namespace == DEFAULT else desc.namespace
        fmt         = "%-20s %-10s %-10s %-20s %s"
        return fmt % (desc.name, namespace, type_name, default, help)
    return '\n'.join(sorted(format(desc) for desc in config_key_descriptions))


def _reset():
    """Used for internal testing."""
    for namespace in configuration_namespaces.values():
        namespace._reset()
    config_key_descriptions[:] = []


def build_getter(validator, getter_namespace=None):
    """Create a getter function for retrieving values from the config cache.
    Getters will default to the DEFAULT namespace.
    """
    def proxy_register(key_name, default=UndefToken, help=None, namespace=None):
        name        = namespace or getter_namespace or DEFAULT
        namespace   = get_namespace(name)
        args        = validator, namespace.get_config_values(), key_name, default
        value_proxy = proxy.ValueProxy(*args)
        namespace.register_proxy(value_proxy)
        add_config_key_description(key_name, validator, default, name, help)
        return value_proxy

    return proxy_register


def has_duplicate_keys(config_data, base_conf, raise_error):
    """Compare two dictionaries for duplicate keys. if raise_error is True
    then raise on exception, otherwise log return True."""
    duplicate_keys = set(base_conf) & set(config_data)
    if not duplicate_keys:
        return
    msg = "Duplicate keys in config: %s" % duplicate_keys
    if raise_error:
        raise errors.ConfigurationError(msg)
    log.info(msg)
    return True


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