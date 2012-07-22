import mock
from testify import run, assert_equal, TestCase, setup, teardown
from testify.assertions import assert_in, assert_raises

from staticconf import config, errors
import staticconf


class BuildGetterTestCase(TestCase):

    def test_build_getter(self):
        validator = mock.Mock()
        getter = config.build_getter(validator)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        assert_in(value_proxy, config.value_proxies)
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, config.configuration_values)


class ValidateKeysTestCase(TestCase):

    @setup
    def setup_value_proxies(self):
        self.patcher = mock.patch('staticconf.config.value_proxies')
        self.log_patcher = mock.patch('staticconf.config.log')
        self.mock_proxies = self.patcher.start()
        self.mock_log = self.log_patcher.start()
        self.keys = ['one', 'two', 'three']

    @teardown
    def teardown_value_proxies(self):
        self.patcher.stop()
        self.log_patcher.stop()

    def test_no_unknown_keys(self):
        proxies = [mock.Mock(config_key=i) for i in self.keys]
        self.mock_proxies.__iter__.return_value = proxies
        config.validate_keys(self.keys, True)
        config.validate_keys(self.keys, False)
        self.mock_log.warn.assert_not_called()

    def test_unknown_warn(self):
        proxies = []
        self.mock_proxies.__iter__.return_value = proxies
        config.validate_keys(self.keys, False)
        calls = self.mock_log.warn.mock_calls
        assert_equal(len(calls), 1)

    def test_unknown_raise(self):
        proxies = []
        self.mock_proxies.__iter__.return_value = proxies
        assert_raises(errors.ConfigurationError, config.validate_keys, self.keys, True)


class ReloadTestCase(TestCase):

    def test_reload(self):
        staticconf.DictConfiguration(dict(one='three', seven='nine'))
        one, seven = staticconf.get('one'), staticconf.get('seven')

        staticconf.DictConfiguration(dict(one='ten', seven='el'))
        staticconf.reload()
        assert_equal(one, 'ten')
        assert_equal(seven, 'el')


if __name__ == "__main__":
    run()