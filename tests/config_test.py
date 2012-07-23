import mock
import tempfile
from testify import run, assert_equal, TestCase, setup, teardown
from testify.assertions import assert_raises

from staticconf import config, errors
import staticconf


class BuildGetterTestCase(TestCase):

    def test_build_getter(self):
        validator = mock.Mock()
        getter = config.build_getter(validator)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        assert value_proxy is config.value_proxies[-1]
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, config.configuration_values)
        config.reset()


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


class ConfigurationWatcherTestCase(TestCase):

    @setup
    def setup_config_watcher(self):
        self.loader = mock.Mock()
        file = tempfile.NamedTemporaryFile()
        # Create the file
        file.flush()
        self.filename = file.name
        self.watcher = config.ConfigurationWatcher(
                    self.loader, self.filename, some_kw_arg='something')

    @setup
    def setup_mock_time(self):
        self.patcher = mock.patch('staticconf.config.time')
        self.mock_time = self.patcher.start()
        self.file_patcher = mock.patch('staticconf.config.os.path')
        self.mock_path = self.file_patcher.start()

    @teardown
    def teardown_mock_time(self):
        self.patcher.stop()
        self.file_patcher.stop()

    def test_should_check(self):
        self.watcher.last_check = 123456789

        self.mock_time.time.return_value = 123456789
        # Still current, but no max_interval
        assert self.watcher.should_check

        # With max interval
        self.watcher.max_interval = 3
        assert not self.watcher.should_check

        # Time has passed
        self.mock_time.time.return_value = 123456794
        assert self.watcher.should_check

    def test_file_modified_not_modified(self):
        self.watcher.last_modified = self.mock_path.getmtime.return_value = 222
        self.mock_time.time.return_value = 123456
        assert not self.watcher.file_modified()
        assert_equal(self.watcher.last_check, self.mock_time.time.return_value)

    def test_file_modified_(self):
        self.watcher.last_modified = 123456
        self.mock_time.time.return_value = 123460
        self.mock_path.getmtime.return_value = self.watcher.last_modified + 200

        assert self.watcher.file_modified()
        assert_equal(self.watcher.last_check, self.mock_time.time.return_value)

    def test_reload(self):
        self.watcher.reload()
        self.loader.assert_called_with(self.filename, some_kw_arg='something')

if __name__ == "__main__":
    run()
