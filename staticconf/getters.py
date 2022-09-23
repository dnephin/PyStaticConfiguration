"""
Functions used to retrieve proxies around values in a
:class:`staticconf.config.ConfigNamespace`. All of the getter methods
return a :class:`ValueProxy`. These proxies are wrappers around a configuration
value. They don't access the configuration until some attribute of the object
is accessed.


.. warning::

    This module should be considered deprecated. There are edge cases which
    make these getters non-obvious to use (such as passing a :class:`ValueProxy`
    to a cmodule.

    Please use :class:`staticconf.readers` if you don't need static
    definitions, or :class:`staticconf.schema` if you do.


Example
-------

.. code-block:: python

    import staticconf

    # Returns a ValueProxy which can be used just like an int
    max_cycles = staticconf.get_int('max_cycles')
    print "Half of max_cycles", max_cycles / 2

    # Using a NamespaceGetters object to retrieve from a namespace
    config = staticconf.NamespaceGetters('special')
    ratio = config.get_float('ratio')


To retrieve values from a namespace, you can create a ``NamespaceGetters``
object.

.. code-block:: python

    my_package_conf = staticconf.NamespaceGetters('my_package_namespace')
    max_size = my_package_conf.get_int('max_size')
    error_msg = my_package_conf.get_string('error_msg')



Arguments
---------

Getters accept the following kwargs:

config_key
    string configuration key
default
    if no ``default`` is given, the key must be present in the configuration.
    Raises ConfigurationError on missing key.
help
    a help string describing the purpose of the config value. See
    :func:`staticconf.config.view_help()`.
namespace
    get the value from this namespace instead of DEFAULT.

"""

from staticconf import config, proxy, readers
from staticconf.config import ConfigGetValue
from staticconf.config import ConfigNamespace
from staticconf.proxy import UndefToken
from staticconf.validation import Validator
from staticconf.proxy import ValueProxy
from typing import Any
from typing import Dict
from typing import Optional


def register_value_proxy(
    namespace: ConfigNamespace,
    value_proxy: ValueProxy,
    help_text: Optional[str]
) -> None:
    """Register a value proxy with the namespace, and add the help_text."""
    namespace.register_proxy(value_proxy)
    config.config_help.add(
        value_proxy.config_key, value_proxy.validator, value_proxy.default,
        namespace.get_name(), help_text)


class ProxyFactory:
    """Create ValueProxy objects so that there is never a duplicate
    proxy for any (namespace, validator, config_key, default) group.
    """

    def __init__(self) -> None:
        self.proxies: Dict[str, ValueProxy] = {}

    def build(
        self,
        validator: Validator,
        namespace: ConfigNamespace,
        config_key: str,
        default: Any,
        help: Optional[str]
    ) -> ValueProxy:
        """Build or retrieve a ValueProxy from the attributes. Proxies are
        keyed using a repr because default values can be mutable types.
        """
        proxy_attrs = validator, namespace, config_key, default
        proxy_key = repr(proxy_attrs)
        if proxy_key in self.proxies:
            return self.proxies[proxy_key]

        value_proxy = proxy.ValueProxy(*proxy_attrs)
        register_value_proxy(namespace, value_proxy, help)
        return self.proxies.setdefault(proxy_key, value_proxy)


proxy_factory = ProxyFactory()


def build_getter(
    validator: Validator,
    getter_namespace: Optional[str] = None
) -> ConfigGetValue:
    """Create a getter function for retrieving values from the config cache.
    Getters will default to the DEFAULT namespace.
    """
    def proxy_register(
        key_name: str,
        default: Any = UndefToken,
        help: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> ValueProxy:
        name        = namespace or getter_namespace or config.DEFAULT
        config_namespace   = config.get_namespace(name)
        return proxy_factory.build(
            validator,
            config_namespace,
            key_name,
            default,
            help
        )

    return proxy_register


class GetterNameFactory:

    @staticmethod
    def get_name(validator_name: str) -> str:
        return 'get_%s' % validator_name if validator_name else 'get'

    @staticmethod
    def get_list_of_name(validator_name: str) -> str:
        return 'get_list_of_%s' % validator_name


NamespaceGetters = readers.build_accessor_type(GetterNameFactory, build_getter)


default_getters = NamespaceGetters(config.DEFAULT)
globals().update(default_getters.get_methods())

__all__ = ['NamespaceGetters'] + list(default_getters.get_methods())
