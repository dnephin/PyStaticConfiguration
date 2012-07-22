PyStaticConfiguration
=====================

A python library for loading static configuration modeled after
Java Apache Commons Configuration.

This library provides the following:

* load configuration data from a file (see below for supported formats)
* data type validation (datetime, date, time, bool, int, float, string)
* override config values from the command line (see examples)
* composite configurations from multiple sources
* configuration can be reloaded


### Why use PyStaticConfiguration?

* it makes your configuration flexible
* it handles overriding default configuration (from command line, environment
 variables, or other configuration files)
* it allows you to define your configuration keys statically at import time,
  and defer loading the configuration until later (after optparse for example)
* it supports reloading the config when a file changes
* it has complete test coverage
* it is easily extensible


Supported Formats
-----------------

* YaML
* XML
* JSON
* Property files
* INI files in a format supported by the `ConfigParser` module
* Python modules
* Python dictionaries
* Python lists with 'key=value' items


Install
-------

`python setup.py install`, etc


Documentation
-------------


### Use the configuration

The following calls are used to retrieve a value from the configuration.  They
can be called at import time before a configuration has been loaded, but
trying to use the returned value before a configuration is loaded will raise
`ConfigurationError`.

    staticconf.get(config_key, [default=None])
    staticconf.get_bool(config_key, [default=None])
    staticconf.get_string(config_key, [default=None])
    staticconf.get_int(config_key, [default=None])
    staticconf.get_float(config_key, [default=None])
    staticconf.get_date(config_key, [default=None])
    staticconf.get_datetime(config_key, [default=None])
    staticconf.get_time(config_key, [default=None])

        config_key: string configuration key
        default:    if no `default` is given, the key must be present in the
                    configuration. Raises ConfigurationError on missing key.

        returns a proxy around the future configuration value. This object can
        be used directly as the proxied object.

        raises `ConfigurationError` if the value in the config fails to validate.


### Load the configuration

Load one or more configurations using the following methods. Each configuration
overrides any duplicate keys in the previous.

    staticconf.AutoConfiguration(base_dir='.', ...)
    staticconf.YamlConfiguration(filename, ...)
    staticconf.JSONConfiguration(filename, ...)
    staticconf.INIConfiguration(filename, ...)
    staticconf.XMLConfiguration(filename, ...)
    staticconf.PropertiesConfiguration(filename, ...)
    staticconf.ListConfiguration(sequence, ...)
    staticconf.DictConfiguration(dict, ...)
    staticconf.PythonConfiguration(module_name, ...)

        These keyword params are supported by all configuration loaders:

        error_on_unknown:   raises an error if there are keys in the config that
                            have not been retrieved (using get_*).
        optional:           if True only warns on failure to load configuration

        returns the loaded configuration dictionary. This dictionary is added
        to the static configuration, and can be accessed using the getters.


### Reload the configuration

A new configuration should be loaded immediately before `reload`.

    staticconf.YamlConfiguration(...)
    staticconf.reload()


Notes
-----

* Properties files only support `=` and `:` key value separators. Keys without
  a separator, and space separators are not supported. Comments (`#`) and blank
  lines are accepted.

Examples
--------
Most trivial example:

    # Look for a config file in a standard location and load it (ex: config.yaml)
    staticconf.AutoConfiguration(base_dir='./config')
    print staticconfig.get('a_value')

    # Similar to above, but allow config values to be overridden using the command line
    import sys, optparse
    parser = optparser.OptionParser()
    parser.add_option('-C', '--config', action='append')
    opts, _ = parser.parse_args()
    staticconf.AutoConfiguration()
    staticconf.ListConfiguration(opts.config)

    # Allow environment variables to override defaults
    import os
    staticconf.AutoConfiguration()
    staticconf.DictConfiguration(os.environ)

Using a YaML file, raise an exception if there are any unexpected configuration
keys in the file.

    # Load a config from a YaML file
    staticconf.YamlConfiguration('my_config.yaml', error_on_unknown=True)


A composite configuration:

    # Load config from xml, and override with custom.json, and opts
    staticconf.XMLConfiguration('default_settings.xml')
    staticconf.JSONConfinfiguration('custom.json')
    staticconf.ListConfiguration(opts.config)


Use these values in your code:

    class SomethingUseful(object):

        max_value = staticconf.get_int('useful.max_value', default=100)
        ratio     = staticconf.get_float('useful.ratio')
        msg       = staticconf.get('useful.msg_string', default="Welcome")

