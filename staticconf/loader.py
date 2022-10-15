"""
Load configuration values from different file formats and python structures.
Nested dictionaries are flattened using dotted notation.

These flattened keys and values are merged into a
:class:`staticconf.config.ConfigNamespace`.

Examples
--------

Basic example:

.. code-block:: python

    staticconf.YamlConfiguration('config.yaml')


Multiple loaders can be used to override values from previous loaders.

.. code-block:: python

    import staticconf

    # Start by loading some values from a defaults file
    staticconf.YamlConfiguration('defaults.yaml')

    # Override with some user specified options
    staticconf.YamlConfiguration('user.yaml', optional=True)

    # Further override with some command line options
    staticconf.ListConfiguration(opts.config_values)


For configuration reloading see :class:`staticconf.config.ConfigFacade`.


Arguments
---------

Configuration loaders accept the following kwargs:

error_on_unknown
    raises a :class:`staticconf.errors.ConfigurationError` if there are keys
    in the config that have not been defined by a getter or a schema.

optional
    if True only warns on failure to load configuration (Default False)

namespace
    load the configuration values into a namespace. Defaults to the
    `DEFAULT` namespace.

flatten
    flatten nested structures into a mapping with depth of 1 (Default True)


.. versionadded:: 0.7.0
    `flatten` was added as a kwarg to all loaders


Custom Loader
-------------

You can create your own loaders for other formats by using
:func:`build_loader()`.  It takes a single argument, a function, which
can accept any arguments, but must return a dictionary of
configuration values.


.. code-block:: python

    from staticconf import loader

    def load_from_db(table_name, conn):
        ...
        return dict((row.field, row.value) for row in cursor.fetchall())

    DBConfiguration = loader.build_loader(load_from_db)

    # Now lets use it
    DBConfiguration('config_table', conn, namespace='special')


"""
import configparser
import logging
import importlib
import os
import re
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

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

ConfigDict = Dict[str, Any]
ConfigLoader = Callable[..., ConfigDict]


def flatten_dict(config_data: ConfigDict) -> Iterator[Tuple[str, Any]]:
    for key, value in config_data.items():
        if hasattr(value, 'items') or hasattr(value, 'iteritems'):
            for k, v in flatten_dict(value):
                yield '{}.{}'.format(key, k), v
            continue

        yield key, value


def load_config_data(
    loader_func: ConfigLoader,
    *args: Any,
    **kwargs: Any
) -> ConfigDict:
    optional = kwargs.pop('optional', False)
    try:
        return loader_func(*args, **kwargs)
    except Exception as e:
        log.info("Optional configuration failed: %s" % e)
        if not optional:
            raise
        return {}


def build_loader(loader_func: ConfigLoader) -> ConfigLoader:
    def loader(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        err_on_unknown      = kwargs.pop('error_on_unknown', False)
        log_keys_only       = kwargs.pop('log_keys_only', True)
        err_on_dupe         = kwargs.pop('error_on_duplicate', False)
        flatten             = kwargs.pop('flatten', True)
        name                = kwargs.pop('namespace', config.DEFAULT)

        config_data = load_config_data(loader_func, *args, **kwargs)
        if flatten:
            config_data = dict(flatten_dict(config_data))
        namespace   = config.get_namespace(name)
        namespace.apply_config_data(
            config_data,
            err_on_unknown,
            err_on_dupe,
            log_keys_only=log_keys_only,
        )
        return config_data

    return loader


def yaml_loader(filename: str) -> ConfigDict:
    import yaml
    try:
        from yaml import CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeLoader  # type: ignore

    with open(filename) as fh:
        return yaml.load(fh, Loader=SafeLoader) or {}


def json_loader(filename: str) -> ConfigDict:
    try:
        import simplejson as json
        assert json
    except ImportError:
        import json  # type: ignore
    with open(filename) as fh:
        return json.load(fh)


def list_loader(seq: List[str]) -> ConfigDict:
    return dict(pair.split('=', 1) for pair in seq)


def auto_loader(
    base_dir: str = '.',
    auto_configurations: Optional[List[Tuple[ConfigLoader, str]]] = None
) -> ConfigDict:
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


def python_loader(module_name: str) -> ConfigDict:
    module = __import__(module_name, fromlist=['*'])
    importlib.reload(module)
    return object_loader(module)


def object_loader(obj: Any) -> ConfigDict:
    return {name: getattr(obj, name)
            for name in dir(obj) if not name.startswith('_')}


def ini_file_loader(filename: str) -> ConfigDict:
    parser = configparser.ConfigParser()
    parser.read([filename])
    config_dict = {}

    for section in parser.sections():
        for key, value in parser.items(section, True):
            config_dict['{}.{}'.format(section, key)] = value

    return config_dict


def xml_loader(filename: str, safe: bool = False) -> ConfigDict:
    from xml.etree import ElementTree

    def build_from_element(element: ElementTree.Element) -> Dict[str, Any]:
        items: Dict[str, Any] = dict(element.items())
        child_items = {
            child.tag: build_from_element(child)
            for child in element}

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


def properties_loader(filename: str) -> ConfigDict:
    split_pattern = re.compile(r'[=:]')

    def parse_line(line: str) -> Optional[Tuple[str, str]]:
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        try:
            key, value = split_pattern.split(line, 1)
        except ValueError:
            msg = "Invalid properties line: %s" % line
            raise errors.ConfigurationError(msg)
        return key.strip(), value.strip()

    with open(filename) as fh:
        return dict(filter(None, (parse_line(line) for line in fh)))


class CompositeConfiguration:
    """Store a list of configuration loaders and their params, so they can
    be reloaded in the correct order.
    """

    def __init__(self, loaders: Optional[List[Any]] = None) -> None:
        self.loaders = loaders or []

    def append(self, loader: Any) -> None:
        self.loaders.append(loader)

    def load(self) -> ConfigDict:
        output = {}
        for loader_with_args in self.loaders:
            output.update(loader_with_args[0](*loader_with_args[1:]))
        return output

    def __call__(self, *args: Any) -> ConfigDict:
        return self.load()


YamlConfiguration = build_loader(yaml_loader)
"""Load configuration from a yaml file.

:param filename: path to a yaml file
"""

JSONConfiguration = build_loader(json_loader)
"""Load configuration from a json file.

:param filename: path to a json file
"""

ListConfiguration = build_loader(list_loader)
"""Load configuration from a list of strings in the form `key=value`.

:param seq: a sequence of strings
"""

DictConfiguration = build_loader(lambda d: d)
"""Load configuration from a :class:`dict`.

:param dict: a dictionary
"""

ObjectConfiguration = build_loader(object_loader)
"""Load configuration from any object. Attributes are keys and the attribute
value are values.

:param object: an object
"""

AutoConfiguration = build_loader(auto_loader)
"""
.. deprecated:: v0.7.0
    Do not use. It will be removed in future versions.
"""


PythonConfiguration = build_loader(python_loader)
"""Load configuration from a python module.

:param module: python path to a module as you would pass it to
    :func:`__import__`
"""


INIConfiguration = build_loader(ini_file_loader)
"""Load configuration from a .ini file

:param filename: path to the ini file
"""


XMLConfiguration = build_loader(xml_loader)
"""Load configuration from an XML file.

:param filename: path to the XML file
"""

PropertiesConfiguration = build_loader(properties_loader)
"""Load configuration from a properties file

:param filename: path to the properties file
"""
