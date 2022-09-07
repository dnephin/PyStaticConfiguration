"""
Store configuration in :class:`ConfigNamespace` objects and provide tools
for reloading, and displaying help messages.


Configuration Reloading
-----------------------

Configuration reloading is supported using a :class:`ConfigFacade`, which
composes a :class:`ConfigurationWatcher` and a :class:`ReloadCallbackChain`.
These classes provide a way of reloading configuration when the file is
modified.
"""
from collections import namedtuple
import hashlib
import logging
import os
import time
import weakref

import six

from staticconf import errors

log = logging.getLogger(__name__)


# Name for the default namespace
DEFAULT = 'DEFAULT'


def remove_by_keys(dictionary, keys):
    keys = set(keys)

    def filter_by_keys(item):
        k, _ = item
        return k not in keys
    return list(filter(filter_by_keys, dictionary.items()))


class ConfigMap:
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


class ConfigNamespace:
    """A container for related configuration values. Values are stored
    using flattened keys which map to values.

    Values are added to this container using :mod:`staticconf.loader`. When a
    :class:`ConfigNamespace` is created, it persists for the entire life of the
    process.  Values will stay in the namespace until :func:`clear` is called
    to remove them.

    To retrieve a namespace, use :func:`get_namespace`.

    To access values stored in this namespace use :mod:`staticconf.readers`
    or :mod:`staticconf.schema`.
    """

    def __init__(self, name):
        self.name = name
        self.configuration_values = {}
        self.value_proxies = weakref.WeakValueDictionary()

    def get_name(self):
        return self.name

    def get_value_proxies(self):
        return list(self.value_proxies.values())

    def register_proxy(self, proxy):
        self.value_proxies[id(proxy)] = proxy

    def apply_config_data(
        self,
        config_data,
        error_on_unknown,
        error_on_dupe,
        log_keys_only=False,
    ):
        self.validate_keys(
            config_data,
            error_on_unknown,
            log_keys_only=log_keys_only,
        )
        self.has_duplicate_keys(config_data, error_on_dupe)
        self.update_values(config_data)

    def update_values(self, *args, **kwargs):
        self.configuration_values.update(*args, **kwargs)

    def get_config_values(self):
        """Return all configuration stored in this object as a dict.
        """
        return self.configuration_values

    def get_config_dict(self):
        """Reconstruct the nested structure of this object's configuration
        and return it as a dict.
        """
        config_dict = {}
        for dotted_key, value in self.get_config_values().items():
            subkeys = dotted_key.split('.')
            d = config_dict
            for key in subkeys:
                d = d.setdefault(key, value if key == subkeys[-1] else {})
        return config_dict

    def get_known_keys(self):
        return {vproxy.config_key for vproxy in self.get_value_proxies()}

    def validate_keys(
        self,
        config_data,
        error_on_unknown,
        log_keys_only=False,
    ):
        unknown = remove_by_keys(config_data, self.get_known_keys())
        if not unknown:
            return

        if log_keys_only:
            unknown = [k for k, _ in unknown]

        msg = "Unexpected value in {} configuration: {}".format(self.name, unknown)
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
        """Remove all values from the namespace."""
        self.configuration_values.clear()

    def _reset(self):
        self.clear()
        self.value_proxies.clear()

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.name)


configuration_namespaces = {DEFAULT: ConfigNamespace(DEFAULT)}


KeyDescription = namedtuple('KeyDescription', 'name validator default help')


def get_namespaces_from_names(name, all_names):
    """Return a generator which yields namespace objects."""
    names = configuration_namespaces.keys() if all_names else [name]
    for name in names:
        yield get_namespace(name)


def get_namespace(name):
    """Return a :class:`ConfigNamespace` by name, creating the
    namespace if it does not exist.
    """
    if name not in configuration_namespaces:
        configuration_namespaces[name] = ConfigNamespace(name)
    return configuration_namespaces[name]


def reload(name=DEFAULT, all_names=False):
    """Reload one or all :class:`ConfigNamespace`. Reload clears the cache of
    :mod:`staticconf.schema` and :mod:`staticconf.getters`, allowing them to
    pickup the latest values in the namespace.

    Defaults to reloading just the DEFAULT namespace.

    :param name: the name of the :class:`ConfigNamespace` to reload
    :param all_names: If True, reload all namespaces, and ignore `name`
    """
    for namespace in get_namespaces_from_names(name, all_names):
        for value_proxy in namespace.get_value_proxies():
            value_proxy.reset()


def validate(name=DEFAULT, all_names=False):
    """Validate all registered keys after loading configuration.

    Missing values or values which do not pass validation raise
    :class:`staticconf.errors.ConfigurationError`. By default only validates
    the `DEFAULT` namespace.

    :param name: the namespace to validate
    :type  name: string
    :param all_names: if True validates all namespaces and ignores `name`
    :type  all_names: boolean
    """
    for namespace in get_namespaces_from_names(name, all_names):
        all(value_proxy.get_value() for value_proxy in namespace.get_value_proxies())


class ConfigHelp:
    """Register and display help messages about config keys."""

    def __init__(self):
        self.descriptions = {}

    def add(self, name, validator, default, namespace, help):
        desc = KeyDescription(name, validator, default, help)
        self.descriptions.setdefault(namespace, []).append(desc)

    def view_help(self):
        """Return a help message describing all the statically configured keys.
        """
        def format_desc(desc):
            return "{} (Type: {}, Default: {})\n{}".format(
                    desc.name,
                    desc.validator.__name__.replace('validate_', ''),
                    desc.default,
                    desc.help or '')

        def format_namespace(key, desc_list):
            return "\nNamespace: {}\n{}".format(
                    key,
                    '\n'.join(sorted(format_desc(desc) for desc in desc_list)))

        def namespace_cmp(item):
            name, _ = item
            return chr(0) if name == DEFAULT else name

        return '\n'.join(format_namespace(*desc) for desc in
                         sorted(self.descriptions.items(),
                                key=namespace_cmp))

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


class ConfigurationWatcher:
    """Watches a file for modification and reloads the configuration
    when it's modified.  Accepts a min_interval to throttle checks.

    The default :func:`reload()` operation is to reload all namespaces. To
    only reload a specific namespace use a :class:`ReloadCallbackChain`
    for the `reloader`.


    .. seealso::

        :func:`ConfigFacade.load` which provides a more concise interface
        for the common case.

    Usage:

    .. code-block:: python

        import staticconf
        from staticconf import config

        def build_configuration(filename, namespace):
            config_loader = partial(staticconf.YamlConfiguration,
                                    filename, namespace=namespace)
            reloader = config.ReloadCallbackChain(namespace)
            return config.ConfigurationWatcher(
                config_loader, filename, min_interval=2, reloader=reloader)

        config_watcher = build_configuration('config.yaml', 'my_namespace')

        # Load the initial configuration
        config_watcher.config_loader()

        # Do some work
        for item in work:
            config_watcher.reload_if_changed()
            ...


    :param config_loader: a function which takes no arguments. It is called
        by :func:`reload_if_changed` if the file has been modified
    :param filenames: a filename or list of filenames to watch for modifications
    :param min_interval: minimum number of seconds to wait between calls to
        :func:`os.path.getmtime` to check if a file has been modified.
    :param reloader: a function which is called after `config_loader` when a
        file has been modified. Defaults to an empty
        :class:`ReloadCallbackChain`
    :param comparators: a list of classes which support the
        :class:`IComparator` interface which are used to determine if a config
        file has been modified. Defaults to :class:`MTimeComparator`.
    """

    def __init__(
            self,
            config_loader,
            filenames,
            min_interval=0,
            reloader=None,
            comparators=None):
        self.config_loader  = config_loader
        self.filenames      = self.get_filename_list(filenames)
        self.min_interval   = min_interval
        self.last_check     = time.time()
        self.reloader       = reloader or ReloadCallbackChain(all_names=True)
        comparators         = comparators or [MTimeComparator]
        self.comparators    = [comp(self.filenames) for comp in comparators]

    def get_filename_list(self, filenames):
        if isinstance(filenames, str):
            filenames = [filenames]
        filenames = sorted(os.path.abspath(name) for name in filenames)
        if not filenames:
            raise ValueError(
                "ConfigurationWatcher requires at least one filename to watch")
        return filenames

    @property
    def should_check(self):
        return self.last_check + self.min_interval <= time.time()

    def reload_if_changed(self, force=False):
        """If the file(s) being watched by this object have changed,
        their configuration will be loaded again using `config_loader`.
        Otherwise this is a noop.

        :param force: If True ignore the `min_interval` and proceed to
            file modified comparisons.  To force a reload use
            :func:`reload` directly.
        """
        if (force or self.should_check) and self.file_modified():
            return self.reload()

    def file_modified(self):
        self.last_check = time.time()
        return any(comp.has_changed() for comp in self.comparators)

    def reload(self):
        config_dict = self.config_loader()
        self.reloader()
        return config_dict

    def get_reloader(self):
        return self.reloader

    def load_config(self):
        return self.config_loader()


class IComparator:
    """Interface for a comparator which is used by :class:`ConfigurationWatcher`
    to determine if a file has been modified since the last check. A comparator
    is used to reduce the work required to reload configuration. Comparators
    should implement a mechanism that is relatively efficient (and scalable),
    so it can be performed frequently.

    :param filenames: A list of absolute paths to configuration files.
    """

    def __init__(self, filenames):
        pass

    def has_changed(self):
        """Returns True if any of the files have been modified since the last
        call to :func:`has_changed`. Returns False otherwise.
        """
        pass


class InodeComparator:
    """Compare files by inode and device number. This is a good comparator to
    use when your files can change multiple times per second.
    """

    def __init__(self, filenames):
        self.filenames = filenames
        self.inodes = self.get_inodes()

    def get_inodes(self):
        def get_inode(stbuf):
            return stbuf.st_dev, stbuf.st_ino
        return [get_inode(os.stat(filename)) for filename in self.filenames]

    def has_changed(self):
        last_inodes, self.inodes = self.inodes, self.get_inodes()
        return last_inodes != self.inodes


def build_compare_func(err_logger=None):
    """Returns a compare_func that can be passed to MTimeComparator.

    The returned compare_func first tries os.path.getmtime(filename),
    then calls err_logger(filename) if that fails. If err_logger is None,
    then it does nothing. err_logger is always called within the context of
    an OSError raised by os.path.getmtime(filename). Information on this
    error can be retrieved by calling sys.exc_info inside of err_logger."""
    def compare_func(filename):
        try:
            return os.path.getmtime(filename)
        except OSError:
            if err_logger is not None:
                err_logger(filename)
        return -1
    return compare_func


class MTimeComparator:
    """Compare files by modified time, or using compare_func,
    if it is not None.

    .. note::

        Most filesystems only store modified time with second grangularity
        so multiple changes within the same second can be ignored.
    """

    def __init__(self, filenames, compare_func=None):
        self.compare_func = (os.path.getmtime if compare_func is None
                             else compare_func)
        self.filenames_mtimes = {
            filename: self.compare_func(filename) for filename in filenames
        }

    def has_changed(self):
        for filename, compare_val in self.filenames_mtimes.items():
            current_compare_val = self.compare_func(filename)
            if compare_val != current_compare_val:
                self.filenames_mtimes[filename] = current_compare_val
                return True

        return False


class MD5Comparator:
    """Compare files by md5 hash of their contents. This comparator will be
    slower for larger files, but is more resilient to modifications which only
    change mtime, but not the files contents.
    """

    def __init__(self, filenames):
        self.filenames = filenames
        self.hashes = self.get_hashes()

    def get_hashes(self):
        def build_hash(filename):
            hasher = hashlib.md5()
            with open(filename, 'rb') as fh:
                hasher.update(fh.read())
            return hasher.digest()
        return [build_hash(filename) for filename in self.filenames]

    def has_changed(self):
        last_hashes, self.hashes = self.hashes, self.get_hashes()
        return last_hashes != self.hashes


class ReloadCallbackChain:
    """A chain of callbacks which will be triggered after configuration is
    reloaded. Designed to work with :class:`ConfigurationWatcher`.

    When this class is called it performs two operations:

    * calls :func:`reload` on the `namespace`
    * calls all attached callbacks

    Usage:

    .. code-block:: python

        chain = ReloadCallbackChain()
        chain.add('some_id', callback_foo)
        chain.add('other_id', other_callback)
        ...

        # some time later
        chain.remove('some_id')

    :param namespace: the name of the namespace to :func:`reload`
    :param all_names: if True :func:`reload` all namespaces and ignore the
                      `namespace` param. Defaults to False
    :param callbacks: initial list of tuples to add to the callback chain
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
        for callback in self.callbacks.values():
            callback()


def build_loader_callable(load_func, filename, namespace):
    def load_configuration():
        get_namespace(namespace).clear()
        return load_func(filename, namespace=namespace)
    return load_configuration


class ConfigFacade:
    """A facade around a :class:`ConfigurationWatcher` and a
    :class:`ReloadCallbackChain`. See :func:`ConfigFacade.load`.

    When a :class:`ConfigFacade` is loaded it will clear the namespace of
    all configuration and load the file into the namespace. If this is not
    the behaviour you want, use a :class:`ConfigurationWatcher` instead.

    Usage:

    .. code-block:: python

        import staticconf

        watcher = staticconf.ConfigFacade.load(
            'config.yaml', # Filename or list of filenames to watch
            'my_namespace',
            staticconf.YamlConfiguration, # Callable which takes the filename
            min_interval=3 # Wait at least 3 seconds before checking modified time
        )

        watcher.add_callback('identifier', do_this_after_reload)
        watcher.reload_if_changed()
    """

    def __init__(self, watcher):
        self.watcher = watcher
        self.callback_chain = watcher.get_reloader()

    @classmethod
    def load(
            cls,
            filename,
            namespace,
            loader_func,
            min_interval=0,
            comparators=None,
    ):
        """Create a new :class:`ConfigurationWatcher` and load the initial
        configuration by calling `loader_func`.

        :param filename: a filename or list of filenames to monitor for changes
        :param namespace: the name of a namespace to use when loading
                          configuration. All config data from `filename` will
                          end up in a :class:`ConfigNamespace` with this name
        :param loader_func: a function which accepts two arguments and uses
                            loader functions from :mod:`staticconf.loader` to
                            load configuration data into a namespace. The
                            arguments are `filename` and `namespace`
        :param min_interval: minimum number of seconds to wait between calls to
                             :func:`os.path.getmtime` to check if a file has
                             been modified.
        :param comparators: a list of classes which support the
            :class:`IComparator` interface which are used to determine if a config
            file has been modified. See ConfigurationWatcher::__init__.
        :returns: a :class:`ConfigFacade`
        """
        watcher = ConfigurationWatcher(
            build_loader_callable(loader_func, filename, namespace=namespace),
            filename,
            min_interval=min_interval,
            reloader=ReloadCallbackChain(namespace=namespace),
            comparators=comparators,
        )
        watcher.load_config()
        return cls(watcher)

    def add_callback(self, identifier, callback):
        self.callback_chain.add(identifier, callback)

    def reload_if_changed(self, force=False):
        """See :func:`ConfigurationWatcher.reload_if_changed` """
        self.watcher.reload_if_changed(force=force)
