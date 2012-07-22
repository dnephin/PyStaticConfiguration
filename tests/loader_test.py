import os
import mock
from testify import assert_equal, TestCase, run, teardown, setup
import tempfile

from staticconf import loader, config

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

    config = """
somekey:
    token: "smarties"
another: blind
    """

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


if __name__ == "__main__":
    run()