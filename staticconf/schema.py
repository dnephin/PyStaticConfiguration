"""
Configuration schemas

Create your own value types using create_value_type(validator).
"""
import functools
from staticconf import validation, proxy, config, errors, getters


class ValueToken(object):
    __slots__ = ['validator', 'config_key', 'default', '_value', 'namespace', 'help']

    def __init__(self, validator, config_key=None, default=proxy.UndefToken, help=None):
        self.validator      = validator
        self.config_key     = config_key
        self.default        = default
        self.help           = help
        self._value         = proxy.UndefToken
        self.namespace      = None

    def set_namespace(self, namespace):
        self.namespace = namespace

    def set_default_config_key(self, config_key):
        """If self.config_key is unset, set it to config_key."""
        self.config_key = self.config_key or config_key

    @proxy.cache_as_field('_value')
    def get_value(self):
        return proxy.extract_value(self)

    def reset(self):
        """Clear the cached value so that configuration can be reloaded."""
        self._value = proxy.UndefToken


def create_value_type(validator):
    return functools.partial(ValueToken, validator)


Int     = create_value_type(validation.validate_int)
String  = create_value_type(validation.validate_string)

# TODO: other types


# TODO: class decorator


def build_property(value_token):
    """Construct a property from a ValueToken. The callable gets passed an
    instance of the schema class, which is ignored.
    """
    def caller(_):
        return value_token.get_value()
    return property(caller)


class SchemaMeta(type):
    """Metaclass to construct config schema object."""

    def __new__(mcs, name, bases, attributes):
        namespace = mcs.get_namespace(attributes)
        attributes = mcs.build_attributes(attributes, namespace)
        return super(SchemaMeta, mcs).__new__(mcs, name, bases, attributes)

    @classmethod
    def get_namespace(cls, attributes):
        if 'namespace' not in attributes:
            raise errors.ConfigurationError("ConfigSchema requires a namespace.")
        return config.get_namespace(attributes['namespace'])

    @classmethod
    def build_attributes(cls, attributes, namespace):
        """Return an attributes dictionary with ValueTokens replaced by a
        property which returns the config value.
        """
        tokens = {}
        def build_token(name, value_token):
            value_token.set_namespace(namespace)
            value_token.set_default_config_key(name)
            getters.register_value_proxy(namespace, value_token, value_token.help)
            tokens[name] = value_token
            return name, build_property(value_token)

        def build_attr(name, attribute):
            if not isinstance(attribute, ValueToken):
                return name, attribute
            return build_token(name, attribute)

        attributes = dict(build_attr(*item) for item in attributes.iteritems())
        attributes['_tokens'] = tokens
        return attributes