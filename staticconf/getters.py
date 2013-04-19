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


def getter_name(validator_name):
    if not validator_name:
        return 'get'
    return 'get_%s' % validator_name


getter_names = [getter_name(name) for name in validation.validators]


__all__ = getter_names + ['NamespaceGetters']


def register_value_proxy(namespace, value_proxy, help_text):
    """Register a value proxy with the namespace, and add the help_text."""
    namespace.register_proxy(value_proxy)
    config.add_config_key_description(
        value_proxy.config_key, value_proxy.validator, value_proxy.default,
        namespace.get_name(), help_text)


def build_getter(validator, getter_namespace=None):
    """Create a getter function for retrieving values from the config cache.
    Getters will default to the DEFAULT namespace.
    """
    def proxy_register(key_name, default=UndefToken, help=None, namespace=None):
        name        = namespace or getter_namespace or config.DEFAULT
        namespace   = config.get_namespace(name)
        value_proxy = proxy.ValueProxy(validator, namespace, key_name, default)
        register_value_proxy(namespace, value_proxy, help)
        return value_proxy

    return proxy_register


class NamespaceGetters(object):
    """An object with getters, which have their namespace already defined."""

    def __init__(self, name):
        self.namespace      = name
        for validator_name, validator in validation.validators.iteritems():
            getter = build_getter(validator, name)
            setattr(self, getter_name(validator_name), getter)


default_getters = NamespaceGetters(config.DEFAULT)
for name in getter_names:
    globals()[name] = getattr(default_getters, name)
