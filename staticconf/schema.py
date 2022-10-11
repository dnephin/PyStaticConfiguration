"""
Configuration schemas can be used to group configuration values
together.  These schemas can be instantiated at import time, and values can
be retrieved from them by accessing the attributes of the schema object.
Each field on the schema turns into an accessor for a configuration value.
These accessors will cache the return value of the validator that they use, so
expensive operations are not repeated.

Example
-------

.. code-block:: python

    from staticconf import schema

    class MyClassSchema(object):
        __metaclass__ = schema.SchemaMeta

        # Namespace to retrieve configuration values from
        namespace = 'my_package'

        # (optional) Config path to prepend to all config keys in this schema
        config_path = 'my_class.foo'

        # Attributes accept the same values as a getter (default, help, etc)
        ratio = schema.float(default=0.2) # configured at my_class.foo.ratio

        # You can optionally specify a different name from the attribute name
        max_threshold = schema.int(config_key='max') # configued at my_class.foo.max


You can also create your schema objects by subclassing Schema

.. code-block:: python

    from staticconf import schema

    class MyClassSchema(schema.Schema):
        ...


Access the values from a schema by instantiating the schema class.

.. code-block:: python

    config = MyClassSchema()
    print config.ratio


Arguments
---------

Schema accessors accept the following kwargs:

config_key
    string configuration key
default
    if no ``default`` is given, the key must be present in the configuration.
    Raises :class:`staticconf.errors.ConfigurationError` on missing key.
help
    a help string describing the purpose of the config value. See
    :func:`staticconf.config.view_help`.



Custom schema types
-------------------

You can also create your own custom types using :func:`build_value_type`.

.. code-block:: python

    from staticconf import schema

    def validator(value):
        try:
            return do_some_casting(value)
        except Exception:
            raise ConfigurationError("%s can't be validated as a foo" % value)

    foo_type = schema.build_value_type(validator)


    class MySchema(object):
        __metaclass__ = schema.SchemaMeta

        something = foo_type(default=...)

"""
import functools
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Type

from staticconf import validation, proxy, config, errors, getters
from staticconf.config import ConfigNamespace
from staticconf.proxy import ValueProxy
from staticconf.validation import Validator


class ValueTypeDefinition:
    __slots__ = ['validator', 'config_key', 'default', 'help']

    def __init__(
        self,
        validator: Validator,
        config_key: Optional[str] = None,
        default: Any = proxy.UndefToken,
        help: Optional[str] = None
    ) -> None:
        self.validator      = validator
        self.config_key     = config_key
        self.default        = default
        self.help           = help


class ValueToken(ValueProxy):
    @classmethod
    def from_definition(
        cls,
        value_def: ValueTypeDefinition,
        namespace: ConfigNamespace,
        key: str
    ) -> "ValueToken":
        return cls(value_def.validator, namespace, key, value_def.default)

    @proxy.cache_as_field('_value')
    def get_value(self) -> Any:
        return proxy.extract_value(self)

    def reset(self) -> None:
        """Clear the cached value so that configuration can be reloaded."""
        self._value = proxy.UndefToken


def build_property(value_token: ValueToken) -> property:
    """Construct a property from a ValueToken. The callable gets passed an
    instance of the schema class, which is ignored.
    """
    def caller(_: Any) -> Any:
        return value_token.get_value()
    return property(caller)


class SchemaMeta(type):
    """Metaclass to construct config schema object."""

    def __new__(
        mcs: Type["SchemaMeta"],
        name: str,
        bases: Tuple[type, ...],
        attributes: Dict[str, Any],
    ) -> "SchemaMeta":
        namespace = mcs.get_namespace(attributes)
        attributes = mcs.build_attributes(attributes, namespace)
        cls = super().__new__(mcs, name, bases, attributes)
        return cast("SchemaMeta", cls)

    @classmethod
    def get_namespace(cls, attributes: Dict[str, Any]) -> ConfigNamespace:
        if 'namespace' not in attributes:
            raise errors.ConfigurationError("ConfigSchema requires a namespace.")
        return config.get_namespace(attributes['namespace'])

    @classmethod
    def build_attributes(
        cls,
        attributes: Dict[str, Any],
        namespace: ConfigNamespace
    ) -> Dict[str, Any]:
        """Return an attributes dictionary with ValueTokens replaced by a
        property which returns the config value.
        """
        config_path = attributes.get('config_path')
        tokens = {}

        def build_config_key(value_def: ValueTypeDefinition, config_key: str) -> str:
            key = value_def.config_key or config_key
            return f"{config_path}.{key}" if config_path else key

        def build_token(
            name: str,
            value_def: ValueTypeDefinition
        ) -> Tuple[str, property]:
            config_key = build_config_key(value_def, name)
            value_token = ValueToken.from_definition(
                                            value_def, namespace, config_key)
            getters.register_value_proxy(namespace, value_token, value_def.help)
            tokens[name] = value_token
            return name, build_property(value_token)

        def build_attr(name: str, attribute: Any) -> Tuple[str, property]:
            if not isinstance(attribute, ValueTypeDefinition):
                return name, attribute
            return build_token(name, attribute)

        attributes = dict(build_attr(*item)
                          for item in attributes.items())
        attributes['_tokens'] = tokens
        return attributes


class Schema(metaclass=SchemaMeta):
    """Base class for configuration schemas, uses :class:`SchemaMeta`."""

    namespace: Optional[str] = None


def build_value_type(validator: Validator) -> Callable[[Any, Any], Any]:
    """A factory function to create a new schema type.

    :param validator: a function which accepts one argument and returns that
                      value as the correct type.
    """
    return functools.partial(ValueTypeDefinition, validator)


# Backwards compatible with staticconf 0.5.2
create_value_type = build_value_type


for name, validator in validation.get_validators():
    name = name or 'any'
    globals()[name] = build_value_type(validator)
    list_of_validator = validation.build_list_type_validator(validator)
    globals()['list_of_%s' % name] = build_value_type(list_of_validator)
