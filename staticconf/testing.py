"""
Facilitate testing of code which uses staticconf.
"""
import copy

from staticconf import config, loader


class MockConfiguration(object):
    """A context manager which replaces the configuration namespace
    while inside the context. When the context exits the old configuration
    values will be restored to that namespace.

    .. code-block:: python

        import staticconf.testing

        config = {
            ...
        }
        with staticconf.testing.MockConfiguration(config, namespace='special'):
            # Run your tests.
        ...


    :param namespace: the namespace to patch
    :param flatten: if True the configuration will be flattened (default True)
    :param args: passed directly to the constructor of :class:`dict` and used
                 as configuration data
    :param kwargs: passed directly to the constructor of :class:`dict` and used
                as configuration data
    """

    def __init__(self, *args, **kwargs):
        name                = kwargs.pop('namespace', config.DEFAULT)
        flatten             = kwargs.pop('flatten', True)
        config_data         = dict(*args, **kwargs)
        self.namespace      = config.get_namespace(name)
        self.config_data    = (dict(loader.flatten_dict(config_data)) if flatten
                              else config_data)
        self.old_values     = None

    def setup(self):
        self.old_values = dict(self.namespace.get_config_values())
        self.reset_namespace(self.config_data)
        config.reload(name=self.namespace.name)

    def teardown(self):
        self.reset_namespace(self.old_values)
        config.reload(name=self.namespace.name)

    def reset_namespace(self, new_values):
        self.namespace.configuration_values.clear()
        self.namespace.update_values(new_values)

    def __enter__(self):
        return self.setup()

    def __exit__(self, *args):
        self.teardown()


class PatchConfiguration(MockConfiguration):
    """A context manager which updates the configuration namespace while inside
    the context. When the context exits the old configuration values will be
    restored to that namespace.

    Unlike MockConfiguration which completely replaces the configuration with
    the new one, this class instead only updates the keys in the configuration
    which are passed to it.  It preserves all previous values that weren't
    updated.

    .. code-block:: python

        import staticconf.testing

        config = {
            ...
        }
        with staticconf.testing.PatchConfiguration(config, namespace='special'):
            # Run your tests.
        ...

    The arguments are identical to MockConfiguration.
    """

    def setup(self):
        self.old_values = copy.deepcopy(dict(self.namespace.get_config_values()))
        new_configuration = copy.deepcopy(self.old_values)
        new_configuration.update(self.config_data)
        self.reset_namespace(new_configuration)
        config.reload(name=self.namespace.name)
