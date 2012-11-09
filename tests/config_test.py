import contextlib
import mock
import tempfile
from testify import run, assert_equal, TestCase, setup, teardown, setup_teardown
from testify.assertions import assert_raises
from testify import class_setup, class_teardown

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

    @class_setup
    def setup_descriptions(self):
        staticconf.get('one', help="the one")
        staticconf.get_time('when', default='NOW', help="The time")
        staticconf.get_bool('you sure', default='No', help='Are you?')
        staticconf.get('one', help="the one", namespace='Beta')
        staticconf.get('one', help="the one", namespace='Alpha')
        staticconf.get('two', help="the two", namespace='Alpha')

    @class_teardown
    def teardown_descriptions(self):
        config._reset()

    @setup
    def setup_lines(self):
        self.lines = config.view_help().split('\n')

        print config.view_help()

    def test_view_help_format(self):
        line, help = self.lines[4:6]
        assert_equal(help, 'The time')
        assert_equal(line, 'when (Type: time, Default: NOW)')

    def test_view_help_format_namespace(self):
        namespace, one, _, two, _, blank = self.lines[9:15]
        assert_equal(namespace, 'Namespace: Alpha')
        assert one.startswith('one')
        assert two.startswith('two')
        assert_equal(blank, '')

    def test_view_help_namespace_sort(self):
        lines = filter(lambda l: l.startswith('Namespace'), self.lines)
        expected = ['Namespace: DEFAULT', 'Namespace: Alpha', 'Namespace: Beta']
        assert_equal(lines, expected)


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

    @setup_teardown
    def setup_mocks_and_config_watcher(self):
        self.loader = mock.Mock()
        with contextlib.nested(
            mock.patch('staticconf.config.time'),
            mock.patch('staticconf.config.os.path'),
            mock.patch('staticconf.config.os.stat'),
            tempfile.NamedTemporaryFile()
        ) as (self.mock_time, self.mock_path, self.mock_stat, file):
            # Create the file
            file.flush()
            self.mock_stat.st_ino=1
            self.mock_stat.st_dev=2
            self.filename = file.name
            self.watcher = config.ConfigurationWatcher(self.loader, self.filename)
            yield

    def test_should_check(self):
        self.watcher.last_check = 123456789

        self.mock_time.time.return_value = 123456789
        # Still current, but no max_interval
        assert self.watcher.should_check

        # With max interval
        self.watcher.min_interval = 3
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

    def test_file_modified_moved(self):
        self.watcher.last_modified = self.mock_path.getmtime.return_value = 123456
        self.mock_time.time.return_value = 123455
        assert not self.watcher.file_modified()
        self.mock_stat.st_ino = 3
        assert self.watcher.file_modified()

    def test_reload_default(self):
        self.watcher.reload()
        self.loader.assert_called_with()

    def test_reload_custom(self):
        reloader = mock.Mock()
        watcher = config.ConfigurationWatcher(
                self.loader, self.filename, reloader=reloader)
        watcher.reload()
        reloader.assert_called_with()

if __name__ == "__main__":
    run()
