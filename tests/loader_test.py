import os
import mock
from testify import assert_equal, TestCase, run, teardown, setup
import tempfile
import textwrap

from staticconf import loader

class LoaderTestCase(TestCase):

    @setup
    def mock_config(self):
        self.patcher = mock.patch('staticconf.config')
        self.mock_config = self.patcher.start()

    @teardown
    def clear_configuration(self):
        self.patcher.stop()


class ListConfigurationTestCase(LoaderTestCase):

    def test_loader(self):
        overrides = ['something=1', 'max=two']
        expected = dict(something='1', max='two')
        config_data = loader.ListConfiguration(overrides)
        assert_equal(config_data, expected)


class FlattenDictTestCase(LoaderTestCase):

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


class YamlConfigurationTestCase(LoaderTestCase):

    config = textwrap.dedent("""
        somekey:
            token: "smarties"
        another: blind
    """)

    def test_loader(self):
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(self.config)
        tmpfile.flush()
        config_data = loader.YamlConfiguration(tmpfile.name)
        assert_equal(config_data['another'], 'blind')
        assert_equal(config_data['somekey.token'], 'smarties')

class JSONConfigurationTestCase(LoaderTestCase):

    config = '{"somekey": {"token": "smarties"}, "another": "blind"}'

    def test_loader(self):
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(self.config)
        tmpfile.flush()
        config_data = loader.JSONConfiguration(tmpfile.name)
        assert_equal(config_data['another'], 'blind')
        assert_equal(config_data['somekey.token'], 'smarties')


class AutoConfigurationTestCase(LoaderTestCase):

    @setup
    def setup_filename(self):
        self.filename = None

    @teardown
    def cleanup_file(self):
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


class PythonConfigurationTestCase(LoaderTestCase):

    module = 'tests.data.example'

    def test_python_configuration(self):
        config_data = loader.PythonConfiguration(self.module)
        assert_equal(config_data['some_value'], 'test')
        assert_equal(config_data['more_values.depth'], 'one')


class INIConfigurationTestCase(LoaderTestCase):

    contents = textwrap.dedent("""
        [Something]
        mars=planet
        stars=sun

        [Business]
        is_good=True
        always=False
        why=not today
    """)

    def test_prop_configuration(self):
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(self.contents)
        tmpfile.flush()
        config_data = loader.INIConfiguration(tmpfile.name)
        assert_equal(config_data['Something.mars'], 'planet')
        assert_equal(config_data['Business.why'], 'not today')


class XMLConfigurationTestCase(TestCase):

    contents = """
        <config>
            <something a="here">
                <depth>1</depth>
                <stars b="there">ok</stars>
            </something>
            <another>foo</another>
        </config>
    """

    def test_xml_configuration(self):
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(self.contents)
        tmpfile.flush()
        config_data = loader.XMLConfiguration(tmpfile.name)
        assert_equal(config_data['something.a'], 'here')
        assert_equal(config_data['something.stars.value'], 'ok')
        assert_equal(config_data['something.stars.b'], 'there')
        assert_equal(config_data['another.value'], 'foo')


if __name__ == "__main__":
    run()