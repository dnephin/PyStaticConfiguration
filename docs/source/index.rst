

PyStaticConfiguration
=================================================

.. toctree::
   :maxdepth: 4

Overview
--------

A python library for loading configuration. Configuration keys are defined
statically, and configuration can be reloaded at any time.  This allows
you to discover missing configuration values immediately, and reload
configuration changes without needing a reference to the configuration
in every object.

See :doc:`modules`

Loading configuration
~~~~~~~~~~~~~~~~~~~~~

Configuration is loaded using one of the configuration loaders in
:mod:`staticconf.loader`. Configuration can be loaded into a namespace
to prevent name collisions. If a configuration is loaded into a namespace the
code which reads it will need to retrieve it from that namespace.

See :ref:`staticconf-loader`

Retrieving configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Configuration is retrieved using a getter from :mod:`staticconf.getters`.
Getters will default to the ``DEFAULT`` namespace. Getters return a proxy
object which will reference a configuration value. After the configuration
is loaded the proxy can be used as the value (in most cases, this will not
work if the value is passed to a c module or checked by isinstance). The
raw underlying value can always be retrieved with the ``.value`` attribute
of the proxy.

See :ref:`staticconf-getters`

Reloading configuration
~~~~~~~~~~~~~~~~~~~~~~~

Configurations can be dynamically reloaded while your application is running.
:mod:`staticconf.config` profiles classes to monitor files, reload the
configuration when they change, and add callbacks to reinitialize afterward.


See :ref:`staticconf-config`

Examples
--------


Loading a configuration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    staticconf.XMLConfiguration('default_settings.xml')
    staticconf.JSONConfinfiguration('custom.json')
    staticconf.ListConfiguration(opts.config)

Retrieving configuration values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class SomethingUseful(object):

        max_value = staticconf.get_int('useful.max_value', default=100)
        ratio     = staticconf.get_float('useful.ratio')
        msg       = staticconf.get('useful.msg_string', default="Welcome")



Putting it all together
~~~~~~~~~~~~~~~~~~~~~~~

An example of a configuration with a single yaml file in a namespace.

.. code-block:: python

    def build_configuration(filename, namespace):
        config_loader = partial(YamlConfiguration, filename, namespace=namespace)
        reloader = ReloadCallbackChain(namespace)
        return ConfigurationWatcher(
            config_loader, filename, min_interval=2, reloader=reloader)

    config_watcher = build_configuration('config.yaml', 'my_namespace')
    # Load the initial configuration
    config_watcher.config_loader()
    # Do some work
    for item in work:
        config_watcher.reload_if_changed()
        ...


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

