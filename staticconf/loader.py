"""
Load configuration data from different file formats and python structures.
Nested dictionaries are flattened using dotted notation.

.. code-block:: python

    staticconf.YamlConfiguration('config.yaml')


You can create your own loaders for other formats by using
``loader.build_loader()``.

.. code-block:: python

    from staticconf import loader
    def custom_loader(*args):
        ...
        return config_dict

    CustomConfiguration = loader.build_loader(custom_loader)

."""
import logging
import os
import itertools
import re
from staticconf import config, errors

__all__ = [
    'YamlConfiguration',
    'JSONConfiguration',
    'ListConfiguration',
    'DictConfiguration',
    'AutoConfiguration',
    'PythonConfiguration',
    'INIConfiguration',
    'XMLConfiguration',
    'PropertiesConfiguration',
    'CompositeConfiguration',
    'ObjectConfiguration',
]


log = logging.getLogger(__name__)


def flatten_dict(config_data):
    for key, value in config_data.iteritems():
        if hasattr(value, 'iteritems'):
            for k, v in flatten_dict(value):
                yield '%s.%s' % (key, k), v
            continue

        yield key, value


def load_config_data(loader_func, *args, **kwargs):
    optional = kwargs.pop('optional', False)
    try:
        return loader_func(*args, **kwargs)
    except Exception, e:
        log.info("Optional configuration failed: %s" % e)
        if not optional:
            raise
        return {}


def build_loader(loader_func):
    def loader(*args, **kwargs):
        err_on_unknown      = kwargs.pop('error_on_unknown', False)
        err_on_dupe         = kwargs.pop('error_on_duplicate', False)
        name                = kwargs.pop('namespace', config.DEFAULT)

        config_data = load_config_data(loader_func, *args, **kwargs)
        config_data = dict(flatten_dict(config_data))
        namespace   = config.get_namespace(name)
        namespace.apply_config_data(config_data, err_on_unknown, err_on_dupe)
        return config_data

    return loader


def yaml_loader(filename):
    import yaml
    with open(filename) as fh:
        return yaml.load(fh) or {}

def json_loader(filename):
    try:
        import simplejson as json
        assert json
    except ImportError:
        import json
    with open(filename) as fh:
        return json.load(fh)


def list_loader(seq):
    return dict(pair.split('=', 1) for pair in seq)


def auto_loader(base_dir='.', auto_configurations=None):
    auto_configurations = auto_configurations or [
        (yaml_loader,       'config.yaml'),
        (json_loader,       'config.json'),
        (ini_file_loader,   'config.ini'),
        (xml_loader,        'config.xml'),
        (properties_loader, 'config.properties')
    ]

    for config_loader, config_arg in auto_configurations:
        path = os.path.join(base_dir, config_arg)
        if os.path.isfile(path):
            return config_loader(path)
    msg = "Failed to auto-load configuration. No configuration files found."
    raise errors.ConfigurationError(msg)


def python_loader(module_name):
    module = __import__(module_name, fromlist=['*'])
    reload(module)
    return object_loader(module)


def object_loader(obj):
    return dict((name, getattr(obj, name))
                for name in dir(obj) if not name.startswith('_'))


def ini_file_loader(filename):
    import ConfigParser
    parser = ConfigParser.SafeConfigParser()
    parser.read([filename])
    config_dict = {}

    for section in parser.sections():
        for key, value in parser.items(section, True):
            config_dict['%s.%s' % (section, key)] = value

    return config_dict


def xml_loader(filename, safe=False):
    from xml.etree import ElementTree

    def build_from_element(element):
        items = dict(element.items())
        child_items = dict(
            (child.tag, build_from_element(child))
            for child in element)

        config.has_duplicate_keys(child_items, items, safe)
        items.update(child_items)
        if element.text:
            if 'value' in items and safe:
                msg = "%s has tag with child or attribute named value."
                raise errors.ConfigurationError(msg % filename)
            items['value'] = element.text
        return items

    tree = ElementTree.parse(filename)
    return build_from_element(tree.getroot())


split_pattern = re.compile(r'[=:]')

def properties_loader(filename):

    def parse_line(line):
        line = line.strip()
        if not line or line.startswith('#'):
            return

        try:
            key, value = split_pattern.split(line, 1)
        except ValueError:
            msg = "Invalid properties line: %s" % line
            raise errors.ConfigurationError(msg)
        return key.strip(), value.strip()

    with open(filename) as fh:
        return dict(itertools.ifilter(None, (parse_line(line) for line in fh)))


class CompositeConfiguration(object):
    """Store a list of configuration loaders and their params, so they can
    be reloaded in the correct order.
    """

    def __init__(self, loaders=None):
        self.loaders = loaders or []

    def append(self, loader):
        self.loaders.append(loader)

    def load(self):
        output = {}
        for loader_with_args in self.loaders:
            output.update(loader_with_args[0](*loader_with_args[1:]))
        return output

    def __call__(self, *args):
        return self.load()


YamlConfiguration       = build_loader(yaml_loader)
JSONConfiguration       = build_loader(json_loader)
ListConfiguration       = build_loader(list_loader)
DictConfiguration       = build_loader(lambda d: d)
ObjectConfiguration     = build_loader(object_loader)
AutoConfiguration       = build_loader(auto_loader)
PythonConfiguration     = build_loader(python_loader)
INIConfiguration        = build_loader(ini_file_loader)
XMLConfiguration        = build_loader(xml_loader)
PropertiesConfiguration = build_loader(properties_loader)
