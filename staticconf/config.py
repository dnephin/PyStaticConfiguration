"""
Classes for storing configuration by namespace, and reloading configuration
while files change.
"""
import logging
import os
import time
from collections import namedtuple
import weakref

from staticconf import errors

log = logging.getLogger(__name__)


# Name for the default namespace
DEFAULT = 'DEFAULT'


def remove_by_keys(dictionary, keys):
    """Remove keys from dict, and return a sequence of key/value pairs."""
    keys = set(keys)
    return filter(lambda (k, v): k not in keys, dictionary.iteritems())


class ConfigMap(object):
    """A ConfigMap can be used to wrap a dictionary in your configuration.
    It will allow you to retain your mapping structure (and prevent it
    from being flattened).
    """
    def __init__(self, *args, **kwargs):
        self.data = dict(*args, **kwargs)

    def __getitem__(self, item):
        return self.data[item]

    def get(self, item, default=None):
        return self.data.get(item, default)

    def __contains__(self, item):
        return item in self.data

    def __len__(self):
        return len(self.data)


class ConfigNamespace(object):
    """A configuration namespace, which contains the list of value proxies
    and configuration values.
    """

    def __init__(self, name):
        self.name = name
        self.configuration_values = {}
        self.value_proxies = weakref.WeakValueDictionary()

    def get_name(self):
        return self.name

    def get_value_proxies(self):
        return self.value_proxies.values()

    def register_proxy(self, proxy):
        """Register a new value proxy in this namespace."""
        self.value_proxies[id(proxy)] = proxy

    def apply_config_data(self, config_data, error_on_unknown, error_on_dupe):
        """Validate, check for duplicates, and update the config."""
        self.validate_keys(config_data, error_on_unknown)
        self.has_duplicate_keys(config_data, error_on_dupe)
        self.update_values(config_data)

    def update_values(self, *args, **kwargs):
        self.configuration_values.update(*args, **kwargs)

    def get_config_values(self):
        return self.configuration_values

    def get_known_keys(self):
        return set(vproxy.config_key for vproxy in self.get_value_proxies())

    def validate_keys(self, config_data, error_on_unknown):
        """Raise an exception if error_on_unknown is true, and keys contains
        a key which is not defined in a registeredValueProxy.
        """
        unknown = remove_by_keys(config_data, self.get_known_keys())
        if not unknown:
            return

        msg = "Unexpected value in %s configuration: %s" % (self.name, unknown)
        if error_on_unknown:
            raise errors.ConfigurationError(msg)
        log.info(msg)

    def has_duplicate_keys(self, config_data, error_on_duplicate):
        args = config_data, self.configuration_values, error_on_duplicate
        return has_duplicate_keys(*args)

    def get(self, item, default=None):
        return self.configuration_values.get(item, default)

    def __getitem__(self, item):
        return self.configuration_values[item]

    def __setitem__(self, key, value):
        self.configuration_values[key] = value

    def __contains__(self, item):
        return item in self.configuration_values

    def clear(self):
        self.configuration_values.clear()

    def _reset(self):
        self.clear()
        self.value_proxies.clear()

    def __str__(self):
        return "%s(%s)" % (type(self).__name__, self.name)


configuration_namespaces = {DEFAULT: ConfigNamespace(DEFAULT)}


KeyDescription = namedtuple('KeyDescription', 'name validator default help')

def get_namespaces_from_names(name, all_names):
    """Return a generator which yields namespace objects."""
    names = configuration_namespaces.keys() if all_names else [name]
    for name in names:
        yield get_namespace(name)


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
    for namespace in get_namespaces_from_names(name, all_names):
        for value_proxy in namespace.get_value_proxies():
            value_proxy.reset()


def validate(name=DEFAULT, all_names=False):
    """Access values in all registered proxies in a namespace. Missing values
    raise ConfigurationError. Defaults to the DEFAULT namespace. If all_names
     is True, validate all namespaces.
    """
    for namespace in get_namespaces_from_names(name, all_names):
        all(bool(value_proxy) for value_proxy in namespace.get_value_proxies())


class ConfigHelp(object):
    """Register and display help messages about config keys."""

    def __init__(self):
        self.descriptions = {}

    def add(self, name, validator, default, namespace, help):
        desc = KeyDescription(name, validator, default, help)
        self.descriptions.setdefault(namespace, []).append(desc)

    def view_help(self):
        """Return a help message describing all the statically configured keys.
        """
        def format(desc):
            help        = desc.help or ''
            type_name   = desc.validator.__name__.replace('validate_', '')
            fmt         = "%s (Type: %s, Default: %s)\n%s"
            return fmt % (desc.name, type_name, desc.default, help)

        def format_namespace(key, desc_list):
            fmt = "\nNamespace: %s\n%s"
            seq = sorted(format(desc) for  desc in desc_list)
            return fmt % (key, '\n'.join(seq))

        def namespace_sort(lhs, rhs):
            if lhs == DEFAULT:
                return -1
            if rhs == DEFAULT:
                return 1
            return lhs < rhs

        seq = sorted(self.descriptions.iteritems(), cmp=namespace_sort)
        return '\n'.join(format_namespace(*desc) for desc in seq)

    def clear(self):
        self.descriptions.clear()


config_help = ConfigHelp()
view_help = config_help.view_help


def _reset():
    """Used for internal testing."""
    for namespace in configuration_namespaces.values():
        namespace._reset()
    config_help.clear()



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
    when it's modified.  Accepts a min_interval to throttle checks.
    """

    def __init__(self, config_loader, filenames, min_interval=0, reloader=None):
        self.config_loader  = config_loader
        self.filenames      = self.get_filename_list(filenames)
        self.inodes         = self._get_inodes()
        self.min_interval   = min_interval
        self.last_check     = time.time()
        self.reloader       = reloader or ReloadCallbackChain(all_names=True)

    def get_filename_list(self, filenames):
        if isinstance(filenames, basestring):
            filenames = [filenames]
        return sorted(os.path.abspath(name) for name in filenames)

    @property
    def should_check(self):
        return self.last_check + self.min_interval <= time.time()

    @property
    def most_recent_changed(self):
        return max(os.path.getmtime(name) for name in self.filenames)

    def _get_inodes(self):
        def get_inode(stbuf):
            return stbuf.st_dev, stbuf.st_ino
        return [get_inode(os.stat(filename)) for filename in self.filenames]

    def reload_if_changed(self, force=False):
        if (force or self.should_check) and self.file_modified():
            return self.reload()

    def file_modified(self):
        prev_check, self.last_check = self.last_check, time.time()
        last_inodes, self.inodes    = self.inodes, self._get_inodes()
        return (last_inodes != self.inodes or
                prev_check < self.most_recent_changed)

    def reload(self):
        config_dict = self.config_loader()
        self.reloader()
        return config_dict

    def get_reloader(self):
        return self.reloader

    def load_config(self):
        return self.config_loader()


class ReloadCallbackChain(object):
    """This object can be used as a convenient way of adding and removing
    callbacks to a ConfigurationWatcher reloader function.
    """

    def __init__(self, namespace=DEFAULT, all_names=False, callbacks=None):
        self.namespace = namespace
        self.all_names = all_names
        self.callbacks = dict(callbacks or ())

    def add(self, identifier, callback):
        self.callbacks[identifier] = callback

    def remove(self, identifier):
        del self.callbacks[identifier]

    def __call__(self):
        reload(name=self.namespace, all_names=self.all_names)
        for callback in self.callbacks.itervalues():
            callback()


def build_loader_callable(load_func, filename, namespace):
    def load_configuration():
        get_namespace(namespace).clear()
        return load_func(filename, namespace=namespace)
    return load_configuration


class ConfigFacade(object):
    """A facade around a ConfigurationWatcher and a ReloadCallbackChain.
    """

    def __init__(self, watcher):
        self.watcher = watcher
        self.callback_chain = watcher.get_reloader()

    @classmethod
    def load(cls, filename, namespace, loader_func, min_interval=0):
        watcher = ConfigurationWatcher(
            build_loader_callable(loader_func, filename, namespace=namespace),
            filename,
            min_interval=min_interval,
            reloader=ReloadCallbackChain(namespace=namespace))
        watcher.load_config()
        return cls(watcher)

    def add_callback(self, identifier, callback):
        self.callback_chain.add(identifier, callback)

    def reload_if_changed(self, force=False):
        self.watcher.reload_if_changed(force=force)
