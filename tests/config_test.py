import mock
import tempfile
from testify import run, assert_equal, TestCase, setup, teardown
from testify.assertions import assert_raises

from staticconf import config, errors
import staticconf


class ConfigurationNamespaceTestCase(TestCase):

    @setup
    def setup_namespace(self):
        self.name = 'the_name'
        self.namespace = config.ConfigNamespace(self.name)
        self.keys = ['one', 'two', 'three']

    def test_register_get_value_proxies(self):
        proxies = [mock.Mock(), mock.Mock()]
        for proxy in proxies:
            self.namespace.register_proxy(proxy)
        assert_equal(self.namespace.get_value_proxies(), proxies)

    def test_update_values(self):
        values = dict(one=1, two=2)
        self.namespace.update_values(values)
        assert 'one' in self.namespace
        assert 'two' in self.namespace

    def test_get_config_values(self):
        self.namespace['stars'] = 'foo'
        values = self.namespace.get_config_values()
        assert_equal(values, {'stars': 'foo'})

    def test_validate_keys_no_unknown_keys(self):
        proxies = [mock.Mock(config_key=i) for i in self.keys]
        self.namespace.value_proxies = proxies
        with mock.patch('staticconf.config.log') as mock_log:
            self.namespace.validate_keys(self.keys, True)
            self.namespace.validate_keys(self.keys, False)
            assert not mock_log.warn.mock_calls

    def test_validate_keys_unknown_warn(self):
        with mock.patch('staticconf.config.log') as mock_log:
            self.namespace.validate_keys(self.keys, False)
            assert_equal(len(mock_log.warn.mock_calls), 1)

    def test_validate_keys_unknown_raise(self):
        assert_raises(errors.ConfigurationError,
                self.namespace.validate_keys, self.keys, True)

class GetNamespaceTestCase(TestCase):

    def test_get_namespace_new(self):
        name = 'some_unlikely_name'
        assert name not in config.configuration_namespaces
        config.get_namespace(name)
        assert name in config.configuration_namespaces

    def test_get_namespace_existing(self):
        name = 'the_common_name'
        namespace = config.get_namespace(name)
        assert_equal(namespace, config.get_namespace(name))


class ReloadTestCase(TestCase):

    @teardown
    def teardown_config(self):
        config._reset()

    def test_reload_default(self):
        staticconf.DictConfiguration(dict(one='three', seven='nine'))
        one, seven = staticconf.get('one'), staticconf.get('seven')

        staticconf.DictConfiguration(dict(one='ten', seven='el'))
        staticconf.reload()
        assert_equal(one, 'ten')
        assert_equal(seven, 'el')

    def test_reload_all(self):
        name = 'another_one'
        staticconf.DictConfiguration(dict(one='three'))
        staticconf.DictConfiguration(dict(two='three'), namespace=name)
        one, two = staticconf.get('one'), staticconf.get('two', namespace=name)
        # access the values to set the value_proxy cache
        _ = bool(one), bool(two)

        staticconf.DictConfiguration(dict(one='four'))
        staticconf.DictConfiguration(dict(two='five'), namespace=name)
        staticconf.reload(all_names=True)
        assert_equal(one, 'four')
        assert_equal(two, 'five')

    def test_reload_single(self):
        name = 'another_one'
        staticconf.DictConfiguration(dict(one='three'))
        staticconf.DictConfiguration(dict(two='three'), namespace=name)
        one, two = staticconf.get('one'), staticconf.get('two', namespace=name)
        # access the values to set the value_proxy cache
        _ = bool(one), bool(two)

        staticconf.DictConfiguration(dict(one='four'))
        staticconf.DictConfiguration(dict(two='five'), namespace=name)
        staticconf.reload()
        assert_equal(one, 'four')
        assert_equal(two, 'three')


class ValidateTestCase(TestCase):

    @teardown
    def teardown_config(self):
        config._reset()

    def test_validate_single_passes(self):
        staticconf.DictConfiguration({})
        config.validate()
        staticconf.get_string('one.two')
        staticconf.DictConfiguration({'one.two': 'nice'})
        config.validate()

    def test_validate_single_fails(self):
        staticconf.get_int('one.two')
        assert_raises(errors.ConfigurationError, config.validate)

    def test_validate_all_passes(self):
        name = 'yan'
        staticconf.DictConfiguration({}, namespace=name)
        staticconf.DictConfiguration({})
        config.validate(all_names=True)
        staticconf.get_string('one.two')
        staticconf.get_string('foo', namespace=name)

        staticconf.DictConfiguration({'one.two': 'nice'})
        staticconf.DictConfiguration({'foo': 'nice'}, namespace=name)
        config.validate(all_names=True)

    def test_validate_all_fails(self):
        name = 'yan'
        staticconf.get_string('foo', namespace=name)
        assert_raises(errors.ConfigurationError, config.validate, all_names=True)


class ViewHelpTestCase(TestCase):

    expected = "%-63s %s\n%-31s %-10s %-21s\n%-31s %-10s %-20s %s" % (
        'one', 'the one', 'when', 'time', 'NOW', 'you sure', 'bool',
        'No', 'Are you?')

    def test_view_help(self):
        staticconf.get('one', help="the one")
        staticconf.get_time('when', default='NOW')
        staticconf.get_bool('you sure', default='No', help='Are you?')

        help_msg = config.view_help()
        assert_equal(help_msg, self.expected)
        config._reset()


class BuildGetterTestCase(TestCase):

    def test_build_getter(self):
        validator = mock.Mock()
        getter = config.build_getter(validator)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(config.DEFAULT)
        assert value_proxy is namespace.get_value_proxies()[-1]
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, namespace.configuration_values)
        config._reset()

    def test_build_getter_with_getter_namespace(self):
        validator = mock.Mock()
        name = 'the stars'
        getter = config.build_getter(validator, getter_namespace=name)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(name)
        assert value_proxy is namespace.get_value_proxies()[-1]
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, namespace.configuration_values)
        config._reset()


class HasDuplicateKeysTestCase(TestCase):

    @setup
    def setup_base_conf(self):
        self.base_conf = {'fear': 'is_the', 'mind': 'killer'}

    def test_has_dupliacte_keys_false(self):
        config_data = dict(unique_keys=123)
        assert not config.has_duplicate_keys(config_data, self.base_conf, True)
        assert not config.has_duplicate_keys(config_data, self.base_conf, False)

    def test_has_duplicate_keys_raises(self):
        config_data = dict(fear=123)
        assert_raises(errors.ConfigurationError,
            config.has_duplicate_keys, config_data, self.base_conf, True)

    def test_has_duplicate_keys_no_raise(self):
        config_data = dict(mind=123)
        assert config.has_duplicate_keys(config_data, self.base_conf, False)


class ConfigurationWatcherTestCase(TestCase):

    @setup
    def setup_config_watcher(self):
        self.loader = mock.Mock()
        file = tempfile.NamedTemporaryFile()
        # Create the file
        file.flush()
        self.filename = file.name
        self.watcher = config.ConfigurationWatcher(self.loader, self.filename)

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

    def test_file_modified(self):
        self.watcher.last_check = 123456
        self.mock_time.time.return_value = 123460
        self.mock_path.getmtime.return_value = self.watcher.last_check + 5

        assert self.watcher.file_modified()
        assert_equal(self.watcher.last_check, self.mock_time.time.return_value)

    def test_reload(self):
        self.watcher.reload()
        self.loader.assert_called_with()


if __name__ == "__main__":
    run()
