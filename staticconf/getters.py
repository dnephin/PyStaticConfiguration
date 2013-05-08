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

from staticconf import validation, config, proxy, readers
from staticconf.proxy import UndefToken


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


class GetterNameFactory(object):

    @staticmethod
    def get_name(validator_name):
        return 'get_%s' % validator_name if validator_name else 'get'

    @staticmethod
    def get_list_of_name(validator_name):
        return 'get_list_of_%s' % validator_name


NamespaceGetters = readers.build_accessor_type(GetterNameFactory, build_getter)


default_getters = NamespaceGetters(config.DEFAULT)
globals().update(default_getters.get_methods())

__all__ = ['NamespaceGetters'] + list(default_getters.get_methods())
