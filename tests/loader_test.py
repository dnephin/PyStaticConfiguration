import os
import tempfile
import textwrap

import pytest
import six
from six.moves import range

from testing.testifycompat import (
    assert_equal,
    assert_raises,
    assert_not_in,
    mock,
)
from staticconf import loader, errors


def get_bytecode_filename(module_name):
    if six.PY2:
        return module_name + '.pyc'
    return __import__(module_name).__cached__


class LoaderTestCase(object):

    content = None

    @pytest.yield_fixture(autouse=True)
    def mock_config(self):
        with mock.patch('staticconf.config') as self.mock_config:
            yield

    @pytest.fixture(autouse=True)
    def write_content_to_file(self, content=None):
        content = content or self.content
        if not content:
            return
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.tmpfile.write(content.encode('utf8'))
        self.tmpfile.flush()


class TestListConfiguration(LoaderTestCase):

    def test_loader(self):
        overrides = ['something=1', 'max=two']
        expected = dict(something='1', max='two')
        config_data = loader.ListConfiguration(overrides)
        assert_equal(config_data, expected)


class TestFlattenDict(LoaderTestCase):

    source = {
        'zero': 0,
        'first': {
            'star': 1,
            'another': {
                'depth': 2
            }
        },
    }

    expected = {
        'zero': 0,
        'first.star': 1,
        'first.another.depth': 2
    }

    def test_flatten(self):
        actual = dict(loader.flatten_dict(self.source))
        assert_equal(actual, self.expected)


class TestBuildLoader(LoaderTestCase):

    def test_build_loader(self):
        loader_func = mock.Mock()
        assert callable(loader.build_loader(loader_func))

    def test_build_loader_optional(self):
        err_msg = "Failed to do"
        loader_func = mock.Mock()
        loader_func.side_effect = ValueError(err_msg)
        config_loader = loader.build_loader(loader_func)

        config_loader(optional=True)
        assert_raises(ValueError, config_loader)

    def test_build_loader_without_flatten(self):
        source = {'base': {'one': 'thing', 'two': 'foo'}}
        loader_func = mock.Mock(return_value=source)
        config_loader = loader.build_loader(loader_func)

        config = config_loader(source, flatten=False)
        assert_equal(config, source)


class TestYamlConfiguration(LoaderTestCase):

    content = textwrap.dedent("""
        somekey:
            token: "smarties"
        another: blind
    """)

    def test_loader(self):
        config_data = loader.YamlConfiguration(self.tmpfile.name)
        assert_equal(config_data['another'], 'blind')
        assert_equal(config_data['somekey.token'], 'smarties')


class TestJSONConfiguration(LoaderTestCase):

    content = '{"somekey": {"token": "smarties"}, "another": "blind"}'

    def test_loader(self):
        config_data = loader.JSONConfiguration(self.tmpfile.name)
        assert_equal(config_data['another'], 'blind')
        assert_equal(config_data['somekey.token'], 'smarties')


class TestAutoConfiguration(LoaderTestCase):

    @pytest.fixture(autouse=True)
    def setup_filename(self):
        self.filename = None

    @pytest.yield_fixture(autouse=True)
    def cleanup_file(self):
        yield
        if self.filename:
            os.unlink(self.filename)

    def test_auto_json(self):
        self.filename = os.path.join(tempfile.gettempdir(), 'config.json')
        with open(self.filename, 'w') as tmpfile:
            tmpfile.write('{"key": "1", "second.value": "two"}')
            tmpfile.flush()
            config_data = loader.AutoConfiguration(base_dir=tempfile.gettempdir())
            assert_equal(config_data['key'], '1')

    def test_auto_yaml(self):
        self.filename = os.path.join(tempfile.gettempdir(), 'config.yaml')
        with open(self.filename, 'w') as tmpfile:
            tmpfile.write('key: 1')
            tmpfile.flush()
            config_data = loader.AutoConfiguration(base_dir=tempfile.gettempdir())
            assert_equal(config_data['key'], 1)

    def test_auto_failed(self):
        assert_raises(errors.ConfigurationError, loader.AutoConfiguration)


class TestPythonConfiguration(LoaderTestCase):

    module          = 'example_mod'
    module_file     = 'example_mod.py'

    module_content  = textwrap.dedent("""
        some_value = "test"

        more_values = {
            "depth": "%s"
        }
    """)

    @pytest.yield_fixture(autouse=True)
    def teardown_module(self):
        yield
        self.remove_module()

    def remove_module(self):
        compiled_file = get_bytecode_filename(self.module)
        for filename in [self.module_file, compiled_file]:
            os.remove(filename) if os.path.exists(filename) else None

    @pytest.fixture(autouse=True)
    def setup_module(self):
        self.create_module('one')

    def create_module(self, value):
        with open(self.module_file, 'w') as fh:
            fh.write(self.module_content % value)

    def test_python_configuration(self):
        config_data = loader.PythonConfiguration(self.module)
        assert_equal(config_data['some_value'], 'test')
        assert_equal(config_data['more_values.depth'], 'one')

    def test_python_configuration_reload(self):
        config_data = loader.PythonConfiguration(self.module)
        assert_equal(config_data['more_values.depth'], 'one')
        self.remove_module()
        self.create_module('two')
        config_data = loader.PythonConfiguration(self.module)
        assert_equal(config_data['more_values.depth'], 'two')


class TestINIConfiguration(LoaderTestCase):

    content = textwrap.dedent("""
        [Something]
        mars=planet
        stars=sun

        [Business]
        is_good=True
        always=False
        why=not today
    """)

    def test_prop_configuration(self):
        config_data = loader.INIConfiguration(self.tmpfile.name)
        assert_equal(config_data['Something.mars'], 'planet')
        assert_equal(config_data['Business.why'], 'not today')


class TestXMLConfiguration(LoaderTestCase):

    content = """
        <config>
            <something a="here">
                <depth>1</depth>
                <stars b="there">ok</stars>
            </something>
            <another>foo</another>
            <empty value="E" />
        </config>
    """

    def test_xml_configuration(self):
        config_data = loader.XMLConfiguration(self.tmpfile.name)
        assert_equal(config_data['something.a'], 'here')
        assert_equal(config_data['something.stars.value'], 'ok')
        assert_equal(config_data['something.stars.b'], 'there')
        assert_equal(config_data['another.value'], 'foo')

    def test_xml_configuration_safe_load(self):
        config_data = loader.XMLConfiguration(self.tmpfile.name, safe=True)
        assert_equal(config_data['something.a'], 'here')
        assert_equal(config_data['empty.value'], 'E')

    def test_xml_configuration_safe_override(self):
        content = """
            <config>
                <sometag foo="bar">
                    <foo>E</foo>
                </sometag>
            </config>
        """
        self.write_content_to_file(content)
        assert_raises(
                errors.ConfigurationError,
                loader.XMLConfiguration,
                self.tmpfile.name,
                safe=True)

    def test_xml_configuration_safe_value_tag(self):
        content = """
            <config>
                <sometag value="snazz">E</sometag>
            </config>
        """
        self.write_content_to_file(content)
        assert_raises(
                errors.ConfigurationError,
                loader.XMLConfiguration,
                self.tmpfile.name,
                safe=True)


class TestPropertiesConfiguration(LoaderTestCase):

    content = textwrap.dedent("""
        stars = in the sky
        blank.key =

        first.second=1
        first.depth.then.more= j=t

        # Ignore the comment
        key with spaces     = the value
        more.props      =          the end

        key.with.col  :   a value
    """)

    def test_properties_configuration(self):
        config_data = loader.PropertiesConfiguration(self.tmpfile.name)
        assert_equal(len(config_data), 7)
        assert_equal(config_data['stars'], 'in the sky')
        assert_equal(config_data['blank.key'], '')
        assert_equal(config_data['first.second'], '1')
        assert_equal(config_data['first.depth.then.more'], 'j=t')
        assert_equal(config_data['key with spaces'], 'the value')
        assert_equal(config_data['more.props'], 'the end')
        assert_equal(config_data['key.with.col'], 'a value')

    def test_invalid_line(self):
        self.tmpfile.write('justkey\n'.encode('utf8'))
        self.tmpfile.flush()
        assert_raises(
                errors.ConfigurationError,
                loader.PropertiesConfiguration,
                self.tmpfile.name)


class TestCompositeConfiguration(object):

    def test_load(self):
        loaders = [(mock.Mock(return_value={i: 0}), 1, 2) for i in range(3)]
        composite = loader.CompositeConfiguration(loaders)
        assert_equal(composite.load(), {0: 0, 1: 0, 2: 0})

        for loader_call, arg_one, arg_two in loaders:
            loader_call.assert_called_with(arg_one, arg_two)


class StubObject(object):
    year = 2012
    month = 3
    hour = 15
    _private = 'something'
    __really_private = 'hidden'


class TestObjectConfiguration(LoaderTestCase):

    def test_load(self):
        config_data = loader.ObjectConfiguration(StubObject)
        assert_equal(config_data['year'], 2012)
        assert_equal(config_data['month'], 3)
        assert_equal(config_data['hour'], 15)
        assert_not_in('_private', config_data)
        assert_not_in('__really_private', config_data)
