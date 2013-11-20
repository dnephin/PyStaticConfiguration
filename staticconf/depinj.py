"""
Dependency injection using staticconf registry.


Register a callable for a key using :func:`register`

.. code-block:: python

    from staticconf import depinj

    # Register a function and its args, a new instance is returned
    depinj.register('TaskRunner',
                    MyTaskRunner,
                    depinj.use('SomeDependencyName'),
                    some_kwarg=True)

    # Register a singleton, always returns the same instance
    deping.register_single('ServiceClient',
                          make_service_client,
                          staticconf.get('host'),
                          staticconf.get('port'))

    
Retreive the dependencies you need for your code.

.. code-block:: python

    from staticconf.deping import use

    runner = use('TaskRunner')
    client = use('ServiceClient')

    runner.run(client.make_request, some_data)


"""
from staticconf import config, proxy


name = "_DEPENDENCIES"
namespace = config.get_namespace(name)


class UnknownDependency(Exception):
    """Raised when a dependency has not been registered."""


class _UnmetDependency(object):
    def __str__(self):
        return "UnmetDepdency"

UnmetDependency = _UnmetDependency()


def register(dep_name, func, *args, **kwargs):
    """Register a callable and its arguments. The callable is executed once
    for each :func:`use`.

    :param dep_name: name of the dependency
    :param func: the callable which returns the dependency
    :param args: arguments passed to the callable
    :param kwargs: keyword arguments passed to the callable
    """
    namespace[dep_name] = func, args, kwargs


class Single(object):
    """Wrap a callable and the result when this class is called."""

    __slots__ = ['func', 'args', 'kwargs', '_instance', '__weakref__']

    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @property
    @proxy.cache_as_field('_instance')
    def instance(self):
        return self.func(*self.args, **self.kwargs)

    def __call__(self):
        return self.instance


def register_single(dep_name, func, *args, **kwargs):
    """Register a callable and its arguments. The callable is executed once
    and the value is cached and returned for each :func:`use`.

    :param dep_name: name of the dependency
    :param func: the callable which returns the dependency
    :param args: arguments passed to the callable
    :param kwargs: keyword arguments passed to the callable
    """
    namespace[dep_name] = Single(func, args, kwargs), [], {}


def use(dep_name):
    """Return a dependency from the registry."""
    return build_dependency_proxy(dep_name)


def build_dependency_proxy(dep_name):

    def instance(func_with_args):
        if func_with_args is UnmetDependency:
            raise UnknownDependency(dep_name)

        func, args, kwargs = func_with_args
        return func(*args, **kwargs)

    return proxy.ValueProxy(instance,
                            namespace,
                            dep_name,
                            default=UnmetDependency)
