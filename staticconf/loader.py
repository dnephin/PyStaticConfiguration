"""Load configuration data from a file."""
import os
from staticconf import config

__all__ = [
    'YamlConfiguration',
    'JSONConfiguration',
    'ListConfiguration',
    'DictConfiguration',
    'AutoConfiguration',
    'PythonConfiguration'
]



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
        config_data         = loader_func(*args, **kwargs)

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


def auto_loader(base_dir='.'):
    auto_configurations = [
        (yaml_loader, 'config.yaml'),
        (json_loader, 'config.json'),
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


YamlConfiguration = build_loader(yaml_loader)
JSONConfiguration = build_loader(json_loader)
ListConfiguration = build_loader(list_loader)
DictConfiguration = build_loader(lambda d: d)
AutoConfiguration = build_loader(auto_loader)
PythonConfiguration = build_loader(python_loader)
