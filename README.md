PyStaticConfiguration
=====================

A python library for loading static configuration modeled after Java  Apache Commons Configuration.

This library provides the following:

* load a configuration from a file (see below for supported formats)
* supports data type validation (datetime, date, int, float, string)
* supports overriding config values from the command line
* support configuration from multiple sources
* stores configuration in a singleton


Supported Formats
-----------------

* YaML
* XML
* JSON
* Config files in a format supported by the `ConfigParser` module
* Python files


Examples
--------
Most trivial example:

    # Look for a config file in a standard location and load it (ex: config.yaml)
    staticconf.AutoConfiguration()
    print staticconfig.get('a_value')

    # Similar to above, but allow config values to be overridden using the command line
    import sys
    import optparse
    parser = optparser.OptionParser()
    parser.add_option('-C', '--config', action='append')
    opts, args = parser.parse_args()
    config = staticconf.AutoConfiguration(overrides=opts.config)


Using a YaML file, raise an exception if there are any unexpected configuration keys set in the file.

    # Load a config from a YaML file
    config = staticconf.YamlConfiguration(file='my_config.yaml', error_on_unknown=True)


A composite configuration:

    # Load config from xml, and override with config in JSON
    config = staticconf.CompositeConfiguration(
                staticconf.XMLConfiguration('default_settings.xml'),
                staticconf.JSONConfinfiguration('custom.json'))


Use these values in your code:

    class SomethingUseful(object):

        max_value = staticconf.get_int('useful.max_value', default=100)
        ratio     = staticconf.get_float('useful.ratio')
        msg       = staticconf.get('useful.msg_string', default="Welcome")

