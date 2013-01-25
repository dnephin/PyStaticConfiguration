"""
Functions used to retrieve values from a ConfigNamespace. To retrieve values
from the default namespace use the module level getters.

.. code-block:: python

    max_size = staticconf.get_int('max_size', default=10)
    threshold = staticconf.get_float('threshold')


To retrieve values from a namespace, you can create a ``NamespaceGetters``
object.

.. code-block:: python

    my_package_conf = staticconf.NamespaceGetters('my_package_namespace')
    max_size = my_package_conf.get_int('max_size')
    error_msg = my_package_conf.get_string('error_msg')

"""

from staticconf import validation, config, proxy
from staticconf.proxy import UndefToken


getter_names = [
    'get',
    'get_bool',
    'get_date',
    'get_datetime',
    'get_float',
    'get_int',
    'get_list',
    'get_set',
    'get_string',
    'get_time',
    'get_tuple',
]


__all__ = getter_names + ['NamespaceGetters']


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


default_getters = NamespaceGetters(config.DEFAULT)
for name in getter_names:
    globals()[name] = getattr(default_getters, name)
