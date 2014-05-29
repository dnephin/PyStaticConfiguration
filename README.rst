PyStaticConfiguration
=====================

A python library for loading and validating configuration. PyStaticConfiguration
has the following design goals:

* separate configuration loading from configuration reading
* provide configuration validation
* support loading configuration from multiple heterogeneous sources
* support transparent configuration reloading
* allow for easy extension of validators and loaders


.. contents:: Contents
    :local:
    :depth: 1
    :backlinks: none



Build Status
------------

.. image:: https://travis-ci.org/dnephin/PyStaticConfiguration.svg?branch=master
    :alt: Travis CI build status
    :target: https://travis-ci.org/dnephin/PyStaticConfiguration




Install
-------

* PyStaticConfiguration is available on pypi: https://pypi.python.org/pypi/PyStaticConfiguration
* The source is hosted on github: https://github.com/dnephin/PyStaticConfiguration

.. code-block:: bash

    $ pip install PyStaticConfiguration


Also see the 
`release notes <http://pythonhosted.org/PyStaticConfiguration/release_notes.html>`_.

Documentation
-------------

http://pythonhosted.org/PyStaticConfiguration/


Overview
--------
PyStaticConfiguration is divided into two operations
`Loading configuration files`_ and `Reading configuration values`_. See
`Advanced usage`_ and `Extending staticconf`_ for more details.


Loading configuration files
---------------------------
PyStaticConfiguration supports loading config values from many file formats
and python structures. See the
`full list of loaders <http://pythonhosted.org/PyStaticConfiguration/staticconf.html#module-staticconf.loader>`_.
When the configuration is loaded, it is put into a ``ConfigNamespace`` object.


Multiple loaders can be used to override values from previous loaders.

.. code-block:: python

    import staticconf

    # Start by loading some values from a defaults file
    staticconf.YamlConfiguration('defaults.yaml')

    # Override with some user specified options
    staticconf.YamlConfiguration('user.yaml', optional=True)

    # Further override with some command line options
    staticconf.ListConfiguration(opts.config_values)

For configuration reloading see `Reloading configuration`_

API docs: :doc:`loader`


Reading configuration values
----------------------------
PyStaticConfiguration supports three methods for retrieving your configuration
values. All of them have a similar set of methods which use validators to
ensure you're getting the type you expect. When a value is missing they will
raise ``staticconf.errors.ConfigurationError`` unless a default was given.
raises ``staticconf.errors.ValidationError`` if the value in the config fails
to validate.

See the `full list of validators <http://pythonhosted.org/PyStaticConfiguration/staticconf.html#module-staticconf.validation>`_. Methods are named using the validator name. For example the methods for getting a
date would be:

* ``staticconf.read_date()``
* ``schema.date()``
* ``staticconf.get_date()``



.. contents::
    :local:
    :backlinks: none

Simple readers
~~~~~~~~~~~~~~
The most direct method for reading config values is through the ``readers``
interface. These readers will return the value from the configuration
namespace after passing them through a validator.

.. code-block:: python

    import staticconf

    # read an int
    max_cycles = staticconf.read_int('max_cycles')
    start_id = staticconf.read_int('poller.init.start_id', default=0)

    # start_date will be a datetime.date
    start_date = staticconf.read_date('start_date')

    # matcher will be a regex object
    matcher = staticconf.read_regex('matcher_pattern')


If you've loaded your config into a namespace (using the namespace
kwarg), you'll need to make sure you're reading your values from that namespace.
This is done through a ``NamespaceReaders`` object, or using the namespace kwarg
on the reader function.

.. code-block:: python

    import staticconf

    # From a namespace, using kwarg
    max_cycles = staticconf.read_int('max_cycles', namespace='iteration')

    # Using a namespace reader
    config = staticconf.NamespaceReaders('iteration')
    max_cycles = config.read_int('max_cycles')
    ratio = config.read_float('ratio')


Readers accept the following kwargs:

config_key
    string configuration key
default
    if no `default` is given, the key must be present in the configuration. Raises ConfigurationError on missing key.
namespace
    get the value from this namespace instead of DEFAULT.


Schemas
~~~~~~~
Configuration schemas can be created to group configuration values
for classes together.  Configuration schemas are created using the
``staticconf.schema`` module. These schemas can be instantiated at import
time, and values can be retrieved from them by accessing the attributes
of the schema object.

.. code-block:: python

    from staticconf import schema

    class SomethingUsefulSchema(schema.Schema):

        # namespace is optional, and will default to DEFAULT
        namespace = 'useful_namespace'

        # This path is prepended to each attribute, so the below schema will
        # expect values at useful.max_value, useful.ratio, etc
        config_path = 'useful'

        max_value = schema.int(default=100)
        ratio     = schema.float()
        msg       = schema.any(config_key='msg_string', default="Welcome")



    config = SomethingUsefulSchema()
    print config.msg


Schema accessors accept the following kwargs:

config_key
    string configuration key
default
    if no ``default`` is given, the key must be present in the configuration. Raises ConfigurationError on missing key.
help
    a help string describing the purpose of the config value. See ``staticconf.view_help()``.


Proxy getters
~~~~~~~~~~~~~
The ``getters`` interface follows the same naming convention, but returns a
``ValueProxy`` instead of the raw value. This has a few advantages over the
``readers`` interface

* these calls can be made at import time, so all expected configuration values are known when the configuration is read.
* when a config is reloaded the proxies will refer to the new value

Note: ``ValueProxy`` objects do not work with c-modules. If you're passing a
value into a c-module, make sure to pass in ``proxy.value`` which is the
underlying raw value.


.. code-block:: python

    import staticconf

    # Returns a ValueProxy which can be used just like an int
    max_cycles = staticconf.get_int('max_cycles')
    print "Half of max_cycles", max_cycles / 2

    # Using a NamespaceGetters object to retrieve from a namespace
    config = staticconf.NamespaceGetters('special')
    ratio = config.get_float('ratio')


Getters accept the following kwargs:

config_key
    string configuration key
default
    if no ``default`` is given, the key must be present in the configuration. Raises ConfigurationError on missing key.
help
    a help string describing the purpose of the config value. See ``staticconf.view_help()``.
namespace
    get the value from this namespace instead of DEFAULT.



Advanced usage
--------------


Reloading configuration
~~~~~~~~~~~~~~~~~~~~~~~

The ``ConfigurationWatcher`` and ``ReloadCallbackChain`` objects are provided
as part of the ``staticconf.config`` module to reload configurations.

``ConfigurationWatcher.reload_if_changed()`` will check if the file has been
modified since the last reload, and reload the configuration when it has.

``ReloadCallbackChain`` is provided to add post-reload callbacks. For most cases
you should be able to create a custom validator to build types from your
configuration data. If that is not possible, this class can be used to
call arbitrary methods after the config is reloaded.

.. code-block:: python

    import staticconf
    from staticconf import config

    def build_configuration(filename, namespace):
        config_loader = partial(staticconf.YamlConfiguration,
                                filename, namespace=namespace)
        reloader = config.ReloadCallbackChain(namespace)
        return config.ConfigurationWatcher(
            config_loader, filename, min_interval=2, reloader=reloader)

    config_watcher = build_configuration('config.yaml', 'my_namespace')

    # Load the initial configuration
    config_watcher.config_loader()

    # Do some work
    for item in work:
        config_watcher.reload_if_changed()
        ...


ConfigFacade
~~~~~~~~~~~~
A ``ConfigFacade`` wraps up the ``ConfigurationWatcher`` and 
``ReloadCallbackChain`` in a nicer interface for the most common case.

.. code-block:: python

    import staticconf

    watcher = staticconf.ConfigFacade.load(
        'config.yaml', # Filename or list of filenames to watch
        'my_namespace',
        staticconf.YamlConfiguration, # Callable which takes the filename
        min_interval=3 # Wait at least 3 seconds before checking modified time
    )

    watcher.add_callback('identifier', do_this_after_reload)
    watcher.reload_if_changed()


Extending staticconf
--------------------

Building configuration loaders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``staticconf.loader.build_loader`` can be used to create new configuration loaders.
It takes a single argument which is a function. The function can accept any
arguments, but must return a dictionary of configuration values.

.. code-block:: python

    from staticconf import loader

    def load_from_db(table_name, conn):
        """Load configuration from a database table."""
        ....
        return dict((row.field, row.value) for row in cursor.fetchall())

    DBConfiguration = loader.build_loader(load_from_db)

    # Now lets use it
    DBConfiguration('config_table', conn, namespace='special')



Building custom getters or readers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both ``staticconf.getters`` and ``staticconf.readers`` provide a similar mechanism
for creating a function to retrieve values from the configuration from a
validation function. A validation function should handle all exceptions and
raise a ValidationError if there is a problem.  It should return the constructed
value.

First create a validation function

.. code-block:: python

    def validate_currency(value):
        try:
            # Assume a tuple or a list
            name, decimal_points = value
            return Currency(name, decimal_points)
        except Exception, e:
            raise ValidationErrror(...)


Example of a getter

.. code-block:: python

    from staticconf import getters

    # A getter without a default namespace
    get_currency = getters.build_getter(validate_currency)

    # A getter with a default namespace
    get_currency = getters.build_getter(validate_currency, getter_namespace='special')

    # Use the getter like any other staticconf getter
    usd = get_currency('currencies.usd', namespace='money_stuff')

Example of a reader

.. code-block:: python

    from staticconf import readers

    read_currency = readers.build_reader(validate_currency)


Building custom schema types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Building custom types for a schema is the same idea. Using the
``validate_currency()`` example from above:

.. code-block:: python

    from staticconf import schema

    currency = schema.build_value_type(validate_currency)

    class PaymentSchema(object):

        error_msg = schema.string()
        usd = currency()
        cdn = currency()

    # And use it
    config = PaymentSchema()
    print config.usd


Reading dicts
-------------
By default PyStaticConfiguration flattens all the values it receives from
the loaders. There are two ways to get dicts from a loader.

Disable Flatten
~~~~~~~~~~~~~~~

You can call loaders with the kwargs ``flatten=False``.

Example:

.. code-block:: python

    YamlConfiguration(filename, flatten=False)

The disadvantage with this approach is that the entire config file will
preserve its nested structure, so you lose out of the ability to easily
merge and override configuration files.

Custom Reader
~~~~~~~~~~~~~

The second option is to represent a dict structures using lists of values
(either a list of pairs or a list of dicts). This list can then be converted
into a dict mapping using a custom getter/reader.

Below are some examples on how this is done. The ``readers`` interface is used as
an example, but the same can be done for the ``getters`` and ``schema`` interface
by replacing ``readers.build_reader()`` with ``getters.build_getter()`` and
``schema.build_value_type()``.


Create a reader which translates a list of dicts into a mapping

.. code-block:: python

    from staticconf import validation, readers

    def build_map_from_key_value(item):
        return item['key'], item['value']

    read_mapping = readers.build_reader(
        validation.build_map_type_validator(build_map_from_key_value))

    my_mapping = read_mapping('config_key_of_a_list_of_dicts')


Create a reader which translates a list of pairs into a mapping

.. code-block:: python

    from staticconf import validation, readers

    read_mapping = readers.build_reader(
        validation.build_map_type_validator(tuple))

    my_mapping = read_mapping('config_key_of_a_list_of_pairs')

Create a reader from translates a list of complex dicts into a mapping

.. code-block:: python

    from staticconf import validation, readers

    def build_map_from_dicts(item):
        return item.pop('name'), item

    read_mapping = readers.build_reader(
        validation.build_map_type_validator(build_map_from_dicts))

    my_mapping = read_mapping('config_key_of_a_list_of_dicts')


