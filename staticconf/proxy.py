"""
Proxy a configuration value. Defers the lookup until the value is used, so that
values can be read statically at import time.
"""
import functools
import operator
from typing import Any
from typing import Callable
from typing import cast
from typing import Type
from typing import TypeVar
from typing import TYPE_CHECKING

from staticconf import errors
from staticconf.validation import Validator


if TYPE_CHECKING:
    from staticconf.config import ConfigNamespace


class UndefTokenType:
    """A token to represent an undefined value, so that None can be used
    as a default value.
    """
    def __repr__(self) -> str:
        return "<Undefined>"


UndefToken = UndefTokenType()


_special_names = [
    '__abs__', '__add__', '__and__', '__bool__', '__call__', '__cmp__',
    '__coerce__',
    '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
    '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
    '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
    '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
    '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
    '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
    '__rand__', '__rdiv__', '__rdivmod__',
    '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
    '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
    '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
    '__truediv__', '__xor__', 'next', '__nonzero__', '__str__', '__unicode__',
    '__index__', '__fspath__',
]


def identity(x: Any) -> Any:
    return x


unary_funcs = {
    '__unicode__':  cast(Callable[[Any], Any], str),
    '__str__':      cast(Callable[[Any], Any], str),
    '__fspath__':   identity,  # python3.6+ os.PathLike interface
    '__repr__':     cast(Callable[[Any], Any], repr),
    '__nonzero__':  cast(Callable[[Any], Any], bool),  # Python2 bool
    '__bool__':     cast(Callable[[Any], Any], bool),  # Python3 bool
    '__hash__':     cast(Callable[[Any], Any], hash),
}


def build_class_def(cls: Type["ValueProxy"]) -> type:
    def build_method(name: str) -> Callable[["ValueProxy", Any, Any], Any]:
        def method(self: "ValueProxy", *args: Any, **kwargs: Any) -> Any:
            if name in unary_funcs:
                return unary_funcs[name](self.value)

            if hasattr(operator, name):
                return getattr(operator, name)(self.value, *args)

            return getattr(self.value, name)(*args, **kwargs)
        return method

    namespace = {name: build_method(name) for name in _special_names}
    return type(cls.__name__, (cls,), namespace)


F = TypeVar("F", bound=Callable[..., Any])


def cache_as_field(cache_name: str) -> Callable[[F], F]:
    """Cache a functions return value as the field 'cache_name'."""
    def cache_wrapper(func: F) -> F:
        @functools.wraps(func)
        def inner_wrapper(self: object, *args: Any, **kwargs: Any) -> Any:
            value = getattr(self, cache_name, UndefToken)
            if value != UndefToken:
                return value

            ret = func(self, *args, **kwargs)
            setattr(self, cache_name, ret)
            return ret
        return cast(F, inner_wrapper)
    return cache_wrapper


def extract_value(proxy: "ValueProxy") -> Any:
    """Given a value proxy type, Retrieve a value from a namespace, raising
    exception if no value is found, or the value does not validate.
    """
    value = proxy.namespace.get(proxy.config_key, proxy.default)
    if value is UndefToken:
        raise errors.ConfigurationError("%s is missing value for: %s" %
            (proxy.namespace, proxy.config_key))

    try:
        return proxy.validator(value)
    except errors.ValidationError as e:
        raise errors.ConfigurationError("%s failed to validate %s: %s" %
            (proxy.namespace, proxy.config_key, e))


class ValueProxy:
    """Proxy a configuration value so it can be loaded after import time."""
    __slots__ = [
        'validator',
        'config_key',
        'default',
        '_value',
        'namespace',
        '__weakref__'
    ]

    @classmethod
    @cache_as_field('_class_def')
    def get_class_def(cls) -> type:
        return build_class_def(cls)

    def __new__(cls, *args: Any, **kwargs: Any) -> "ValueProxy":
        """Create instances of this class with proxied special names."""
        klass = cast(Type["ValueProxy"], cls.get_class_def())
        instance = cast("ValueProxy", object.__new__(klass))
        klass.__init__(instance, *args, **kwargs)
        return instance

    def __init__(
        self,
        validator: Validator,
        namespace: "ConfigNamespace",
        key: str,
        default: Any = UndefToken,
    ) -> None:
        self.validator      = validator
        self.config_key     = key
        self.default        = default
        self.namespace      = namespace
        self._value         = UndefToken

    @cache_as_field('_value')
    def get_value(self) -> Any:
        return extract_value(self)

    value = property(get_value)

    def __getattr__(self, item: str) -> Any:
        return getattr(self.value, item)

    def reset(self) -> None:
        """Clear the cached value so that configuration can be reloaded."""
        self._value = UndefToken
