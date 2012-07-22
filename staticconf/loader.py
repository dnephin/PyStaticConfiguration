"""
Load configuration data from different file formats and python structures.
Nested dictionaries are flattened using dotted notation.

Create your own loader:

    from staticconf import loader
    def custom_loader(*args):
        ...
        return config_dict
    CustomConfiguration = loader.build_loader(custom_loader)
    CustomConfiguration()


."""
import logging
import os
from staticconf import config

__all__ = [
    'YamlConfiguration',
    'JSONConfiguration',
    'ListConfiguration',
    'DictConfiguration',
    'AutoConfiguration',
    'PythonConfiguration',
    'INIConfiguration',
    'XMLConfiguration'
]


log = logging.getLogger(__name__)


def flatten_dict(config_data):
    for key, value in config_data.iteritems():
        if isinstance(value, dict):
            for k, v in flatten_dict(value):
                yield '%s.%s' % (key, k), v
            continue

        yield key, value


def build_loader(loader_func):
    def loader(*args, **kwargs):
        error_on_unknown    = kwargs.pop('error_on_unknown', False)
        optional            = kwargs.pop('optional', False)

        try:
            config_data     = loader_func(*args, **kwargs)
        except Exception, e:
            log.warn("Optional configuration failed: %s" % e)
            if not optional:
                raise
            return {}

        config_data = dict(flatten_dict(config_data))
        config.validate_keys(config_data.keys(), error_on_unknown)
        config.set_configuration(config_data)
        return config_data

    return loader


def yaml_loader(filename):
    import yaml
    with open(filename) as fh:
        return yaml.load(fh)

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
    ]

    for config_loader, config_arg in auto_configurations:
        path = os.path.join(base_dir, config_arg)
        if os.path.isfile(path):
            return config_loader(path)
    return {}


def python_loader(module_name):
    module = __import__(module_name, fromlist=['*'])
    config_dict = {}
    for name in dir(module):
        if name.startswith('__'):
            continue
        config_dict[name] = getattr(module, name)
    return config_dict


def ini_file_loader(filename):
    import ConfigParser
    parser = ConfigParser.SafeConfigParser()
    parser.read([filename])
    config_dict = {}

    for section in parser.sections():
        for key, value in parser.items(section, True):
            config_dict['%s.%s' % (section, key)] = value

    return config_dict


def xml_loader(filename):
    from xml.etree import ElementTree

    def build_from_element(element):
        items = dict(element.items())
        items.update((child.tag, build_from_element(child)) for child in element)
        # TODO: value overrides, and childs override attributes
        if element.text:
            items['value'] = element.text
        return items

    tree = ElementTree.parse(filename)
    return build_from_element(tree.getroot())


YamlConfiguration   = build_loader(yaml_loader)
JSONConfiguration   = build_loader(json_loader)
ListConfiguration   = build_loader(list_loader)
DictConfiguration   = build_loader(lambda d: d)
AutoConfiguration   = build_loader(auto_loader)
PythonConfiguration = build_loader(python_loader)
INIConfiguration    = build_loader(ini_file_loader)
XMLConfiguration    = build_loader(xml_loader)
