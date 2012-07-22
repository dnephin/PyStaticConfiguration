from testify import assert_equal, TestCase, run, teardown
import tempfile

from staticconf import loader, config

class LoaderTestCase(TestCase):

    @teardown
    def clear_configuration(self):
        config.reset()


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


if __name__ == "__main__":
    run()