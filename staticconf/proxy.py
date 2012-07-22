import operator
from staticconf import validation, errors

class UndefToken(object):
    pass


_special_names = [
    '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
    '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
    '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
    '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
    '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
    '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
    '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
    '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
    '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
    '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
    '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
    '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
    '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
    '__truediv__', '__xor__', 'next', '__nonzero__'
    ]


class ValueProxy(object):
    """Proxy a configuration value so it can be loaded after import time."""

    class_def = None

    def __new__(cls, *args, **kwargs):
        """Create instances of this class with proxied special names."""
        klass = cls.get_class_proxy()
        instance = object.__new__(klass)
        klass.__init__(instance, *args, **kwargs)
        return instance

    def __init__(self, validator, value_cache, name, default=UndefToken):
        self.validator      = validator
        self.name           = name
        self.default        = default
        self.value          = UndefToken
        self.value_cache    = value_cache

    def get_value(self):
        if self.value is not UndefToken:
            return self.value

        value = self.value_cache.get(self.name, self.default)
        if value is UndefToken:
            msg = "Configuration is missing value for: %s"
            raise errors.ConfigurationError(msg % self.name)

        try:
            self.value = self.validator(value)
        except validation.ValidationError, e:
            msg = "Failed to validate %s: %s" % (self.name, e)
            raise errors.ConfigurationError(msg)

        return self.value

    @classmethod
    def get_class_proxy(cls):
        if cls.class_def:
            return cls.class_def

        def build_method(name):
            def method(self, *args, **kw):
                self.get_value()

                if name == '__repr__':
                    return repr(self.value)

                if hasattr(operator, name):
                    return getattr(operator, name)(self.value, *args)

                return getattr(self.value, name)(*args, **kw)
            return method

        namespace = dict((name, build_method(name)) for name in _special_names)
        cls.class_def = type(cls.__name__, (cls,), namespace)
        return cls.class_def
