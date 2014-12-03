Overview
========

:mod:`staticconf` is a library for loading configuration values from many 
heterogeneous formats and reading those values. This process is split into two 
phases.

Configuration Loading
---------------------

Configuration is read from files or python objects (:class:`dict`,
:class:`list`, or any :class:`object` with attributes), flattened, and merged
into a container called a :class:`staticconf.config.ConfigNamespace`.
Namespaces are used to group related configuration together.

If configuration is changed frequently, it can also be reloaded easily
with very little change to the existing code.


See :mod:`staticconf.loader` for a list of supported file formats and config
loading examples.

See :func:`staticconf.config.ConfigFacade.load` for examples of building
a reloader.

See :class:`staticconf.config.ConfigNamespace` for more details about
namespaces.



Reading configuration values
----------------------------
Once configuration data is loaded into a 
:class:`staticconf.config.ConfigNamespace` there are three options for
retrieving the configuration values. All of them have a similar set of methods
which use validators to ensure you're getting the type you expect. When a value
is missing they will raise :class:`staticconf.errors.ConfigurationError` unless
a default was given.  They will raises
:class:`staticconf.errors.ValidationError` if the value in the config fails to
validate.

The list of provided validators is :mod:`staticconf.validation`, but you can 
create custom validators for any type. Functions for reading 
configuration values are named using a convention based on the validator name.
For example the methods for getting a date using 
:func:`staticconf.validation.validate_date` would be:

* ``staticconf.read_date()``
* ``schema.date()``
* ``staticconf.get_date()``


Readers
~~~~~~~

:mod:`staticconf.readers`

Readers are the most straightforward option. They simply lookup the value in
the namespace and return it. There is no caching of the type-coercion.


Schema
~~~~~~

:mod:`staticconf.schema`

Schemas are classes where each property is an accessor for a configuration
value. The type-coercion is cached on the class. This can be useful if you're
performing more involved coercion (such as converting a large list to a
mapping, or building complex types).


Getters
~~~~~~~

:mod:`staticconf.getters`

Getters have the same properties as schema accessors, but do not use a class.
See the module documentation for some limitations with this option.



Example
-------

For this example we'll use yaml configuration files. Given two files,
a `application.yaml`:

.. code-block:: yaml

    pid: /var/run/app1.pid

    storage_paths:
        - /mnt/storage
        - /mnt/nfs

    min_date: 2014-12-12

    groups:
        users:
            - userone
            - usertwo
        admins:
            - admin
        

And an `overrides.yaml`

.. code-block:: yaml

    max_files: 10

    groups:
        users:
            - customuser


First load some configuration from a file. This is often done during the 
"startup" phase of an application, such as after :mod:`argparse` has completed
(potentially where one of the command line args is a config filename). For a
web application, this might happen during the initialization of the webapp.

.. code-block:: python

    import staticconf

    app_config = 'application.yaml'
    app_custom = 'overrides.yaml'

    YamlConfiguration(app_config)
    YamlConfiguration(app_custom, optional=True)


Now we've loaded up our application config, and overridden it with the data
from `overrides.yaml`. `overrides.yaml` was optional, so if the file was missing
there would be no error.

Next we'll want to read these values at some point.

.. code-block:: python

    import staticconf

    pid = staticconf.read_string('pid')

    storage_paths = staticconf.read_list_of_string('storage_paths')
    
    # This is the just the list of one user `customuser` since we loaded our
    # `overrides.yaml` over the original list
    # Also notice the key was flattened, so we use a dotted notation
    users = staticconf.read_list_of_string('groups.users')

    # Using doted notation allows us to preserve any part of the mapping
    # structure, so in this case, the admins from `application.yaml` are
    # still there
    admins = staticconf.read_list_of_string('groups.admins')

    # We can also read other types. In our config this was a string, but we're
    # reading a date, so we receive a datetime.date object
    min_date = staticconf.read_date('min_date')


See :class:`staticconf.config.ConfigFacade` for examples of how to reload
configuration on changes.


Logging
-------

:mod:`staticconf` logs a message at `INFO` level when configuration is loaded
with the message "Unexpected value in <namespace> configuration: ...", with the
list of unexpected values.  Unexpected values are those that haven't been
registered by a :mod:`staticconf.schema` or :mod:`staticconf.getter`.

This message is used to debug configuration errors. If you'd like to disable it
you can set the logging level for `staticconf.config` to `WARN`.


Reading dicts
-------------
By default :mod:`staticconf` flattens all the values it receives from
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

Below are some examples on how this is done. The :mod:`staticconf.readers`
interface is used as an example, but the same can be done for the 
:mod:`staticconf.getters` and :mod:`staticconf.schema` interfaces
by replacing :func:`staticconf.readers.build_reader` with
:func:`staticconf.getters.build_getter` or
:func:`staticconf.schema.build_value_type`.


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


