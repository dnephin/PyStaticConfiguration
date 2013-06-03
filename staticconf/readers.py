"""
Functions to read values directly from a configuration namespace.  Values
will be validated, but will not be wrapped in a Proxy.

.. code-block:: python

    import staticconf

    max_value = staticconf.read_int('max_value')
    # Read a value from a namespace
    intervals = staticconf.read_float('intervals', namespace='something')


Readers can be attached to a namespace using a NamespaceReaders object.

.. code-block:: python

    import staticconf

    bling_reader = staticconf.NamespaceReader('bling')

    currency = bling_reader.read_string('currency')
    value = bling_reader.read_float('value')

Available reader accessors include:

    - read_bool()
    - read_date()
    - read_datetime()
    - read_float()
    - read_int()
    - read_list()
    - read_list_of_bool()
    - read_list_of_date()
    - read_list_of_datetime()
    - read_list_of_float()
    - read_list_of_int()
    - read_list_of_list()
    - read_list_of_set()
    - read_list_of_time()
    - read_list_of_tuple()
    - read_regex()
    - read_set()
    - read_string()
    - read_tuple()
"""
from staticconf import validation, config, errors
from staticconf.proxy import UndefToken


def _read_config(config_key, config_namespace, default):
    value = config_namespace.get(config_key, default=default)
    if value is UndefToken:
        msg = '%s missing value for %s' % (config_namespace, config_key)
        raise errors.ConfigurationError(msg)
    return value


def build_reader(validator, reader_namespace=config.DEFAULT):
    def reader(config_key, default=UndefToken, namespace=None):
        config_namespace = config.get_namespace(namespace or reader_namespace)
        return validator(_read_config(config_key, config_namespace, default))
    return reader


class ReaderNameFactory(object):
    """Factory used to create the NamespaceReaders object."""

    @staticmethod
    def get_name(name):
        return 'read_%s' % name if name else 'read'

    @staticmethod
    def get_list_of_name(name):
        return 'read_list_of_%s' % name


def get_all_accessors(name_factory):
    for name, validator in validation.get_validators():
        yield name_factory.get_name(name), validator
        yield (name_factory.get_list_of_name(name),
               validation.build_list_type_validator(validator))


class NamespaceAccessor(object):

    def __init__(self, name, accessor_map, builder):
        self.accessor_map       = accessor_map
        self.builder            = builder
        self.namespace          = name

    def __getattr__(self, item):
        if item not in self.accessor_map:
            raise AttributeError(item)
        return self.builder(self.accessor_map[item], self.namespace)

    def get_methods(self):
        return dict((name, getattr(self, name)) for name in self.accessor_map)


def build_accessor_type(name_factory, builder):
    accessor_map = dict(get_all_accessors(name_factory))
    return lambda name: NamespaceAccessor(name, accessor_map, builder)


NamespaceReaders = build_accessor_type(ReaderNameFactory, build_reader)


default_readers = NamespaceReaders(config.DEFAULT)
globals().update(default_readers.get_methods())

__all__ = ['NamespaceReaders'] + list(default_readers.get_methods())
