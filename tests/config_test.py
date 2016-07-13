import gc
import os
import platform
import tempfile
import time
import sys
import functools

import pytest

from testing.testifycompat import (
    assert_equal,
    assert_raises,
    mock,
)
from staticconf import (
    config,
    errors,
    proxy,
    schema,
    testing,
    validation,
)
import staticconf


class TestRemoveByKeys(object):

    def test_empty_dict(self):
        keys = range(3)
        assert_equal([], config.remove_by_keys({}, keys))

    def test_no_keys(self):
        keys = []
        map = dict(enumerate(range(3)))
        assert_equal(list(map.items()), config.remove_by_keys(map, keys))

    def test_overlap(self):
        keys = [1, 3, 5 ,7]
        map = dict(enumerate(range(8)))
        expected = [(0,0), (2, 2), (4, 4), (6, 6)]
        assert_equal(expected, config.remove_by_keys(map, keys))


class TestConfigMap(object):

    @pytest.fixture(autouse=True)
    def setup_config_map(self):
        self.config_map = config.ConfigMap(one=1, three=3, seven=7)

    def test_no_iteritems(self):
        assert not hasattr(self.config_map, 'iteritems')

    def test_getitem(self):
        assert_equal(self.config_map['one'], 1)
        assert_equal(self.config_map['seven'], 7)

    def test_get(self):
        assert_equal(self.config_map.get('three'), 3)
        assert_equal(self.config_map.get('four', 0), 0)

    def test_contains(self):
        assert 'one' in self.config_map
        assert 'two' not in self.config_map

    def test_len(self):
        assert_equal(len(self.config_map), 3)


class TestConfigurationNamespace(object):

    @pytest.fixture(autouse=True)
    def setup_namespace(self):
        self.name = 'the_name'
        self.namespace = config.ConfigNamespace(self.name)
        self.config_data = dict(enumerate(['one', 'two', 'three'], 1))

    def test_register_get_value_proxies(self):
        proxies = [mock.Mock(), mock.Mock()]
        for mock_proxy in proxies:
            self.namespace.register_proxy(mock_proxy)
        assert_equal(self.namespace.get_value_proxies(), proxies)

    @pytest.mark.skipif('PyPy' in platform.python_implementation(), reason="Fails on PyPy")
    def test_get_value_proxies_does_not_contain_out_of_scope_proxies(self):
        assert not self.namespace.get_value_proxies()
        def a_scope():
            mock_proxy = mock.create_autospec(proxy.ValueProxy)
            self.namespace.register_proxy(mock_proxy)

        a_scope()
        a_scope()
        gc.collect()
        assert_equal(len(self.namespace.get_value_proxies()), 0)

    def test_update_values(self):
        values = dict(one=1, two=2)
        self.namespace.update_values(values)
        assert 'one' in self.namespace
        assert 'two' in self.namespace

    def test_get_config_values(self):
        self.namespace['stars'] = 'foo'
        values = self.namespace.get_config_values()
        assert_equal(values, {'stars': 'foo'})

    def test_get_config_dict(self):
        self.namespace['one.two.three.four'] = 5
        self.namespace['one.two.three.five'] = 'six'
        self.namespace['one.b.cats'] = [1, 2, 3]
        self.namespace['a.two'] = 'c'
        self.namespace['first'] = True
        d = self.namespace.get_config_dict()
        assert_equal(d, {
            'one': {
                'b': {
                    'cats': [1, 2, 3],
                },
                'two': {
                    'three': {
                        'four': 5,
                        'five': 'six',
                    },
                },
            },
            'a': {
                'two': 'c',
            },
            'first': True,
        })

    def test_get_known_keys(self):
        proxies = [mock.Mock(), mock.Mock()]
        for mock_proxy in proxies:
            self.namespace.register_proxy(mock_proxy)
        expected = set([mock_proxy.config_key for mock_proxy in proxies])
        assert_equal(self.namespace.get_known_keys(), expected)

    def test_validate_keys_no_unknown_keys(self):
        proxies = [mock.Mock(config_key=i) for i in self.config_data]
        for mock_proxy in proxies:
            self.namespace.register_proxy(mock_proxy)
        with mock.patch('staticconf.config.log') as mock_log:
            self.namespace.validate_keys(self.config_data, True)
            self.namespace.validate_keys(self.config_data, False)
            assert not mock_log.warn.mock_calls

    def test_validate_keys_unknown_log(self):
        with mock.patch('staticconf.config.log') as mock_log:
            self.namespace.validate_keys(self.config_data, False)
            assert_equal(len(mock_log.info.mock_calls), 1)

    def test_validate_keys_unknown_raise(self):
        assert_raises(errors.ConfigurationError,
                self.namespace.validate_keys, self.config_data, True)

    def test_clear(self):
        self.namespace.apply_config_data(self.config_data, False, False)
        assert self.namespace.get_config_values()
        self.namespace.clear()
        assert_equal(self.namespace.get_config_values(), {})


class TestGetNamespace(object):

    @pytest.yield_fixture(autouse=True)
    def mock_namespaces(self):
        with mock.patch.dict(config.configuration_namespaces):
            yield

    def test_get_namespace_new(self):
        name = 'some_unlikely_name'
        assert name not in config.configuration_namespaces
        config.get_namespace(name)
        assert name in config.configuration_namespaces

    def test_get_namespace_existing(self):
        name = 'the_common_name'
        namespace = config.get_namespace(name)
        assert_equal(namespace, config.get_namespace(name))


class TestReload(object):

    @pytest.yield_fixture(autouse=True)
    def mock_namespaces(self):
        with mock.patch.dict(config.configuration_namespaces):
            yield

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
        one.value, two.value

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
        one.value, two.value

        staticconf.DictConfiguration(dict(one='four'))
        staticconf.DictConfiguration(dict(two='five'), namespace=name)
        staticconf.reload()
        assert_equal(one, 'four')
        assert_equal(two, 'three')


class TestValidateConfig(object):

    @pytest.yield_fixture(autouse=True)
    def patch_config(self):
        with mock.patch.dict(config.configuration_namespaces, clear=True):
            with testing.MockConfiguration():
                yield

    def test_validate_single_passes(self):
        staticconf.DictConfiguration({})
        config.validate()
        _ = staticconf.get_string('one.two')
        staticconf.DictConfiguration({'one.two': 'nice'})
        config.validate()

    def test_validate_single_fails(self):
        _ = staticconf.get_int('one.two')
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
        _ = staticconf.get_string('foo', namespace=name)  # flake8: noqa
        assert_raises(errors.ConfigurationError,
                      config.validate,
                      all_names=True)

    def test_validate_value_token(self):
        class ExampleSchema(schema.Schema):
            namespace = 'DEFAULT'

            thing = schema.int()

        assert_raises(errors.ConfigurationError,
                      config.validate,
                      all_names=True)


class TestConfigHelp(object):

    @pytest.fixture(autouse=True)
    def setup_config_help(self):
        self.config_help = config.ConfigHelp()
        self.config_help.add('one',
            validation.validate_any, None, 'DEFAULT', "the one")
        self.config_help.add('when',
            validation.validate_time, 'NOW', 'DEFAULT', "The time")
        self.config_help.add('you sure',
            validation.validate_bool, 'No', 'DEFAULT', "Are you?")
        self.config_help.add('one',
            validation.validate_any, None, 'Beta',  "the one")
        self.config_help.add('one',
            validation.validate_any, None, 'Alpha', "the one")
        self.config_help.add('two',
            validation.validate_any, None, 'Alpha',  "the two")
        self.lines = self.config_help.view_help().split('\n')

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
        lines = list(filter(lambda l: l.startswith('Namespace'), self.lines))
        expected = ['Namespace: DEFAULT', 'Namespace: Alpha', 'Namespace: Beta']
        assert_equal(lines, expected)


class TestHasDuplicateKeys(object):

    @pytest.fixture(autouse=True)
    def setup_base_conf(self):
        self.base_conf = {'fear': 'is_the', 'mind': 'killer'}

    def test_has_dupliacte_keys_false(self):
        config_data = dict(unique_keys=123)
        assert not config.has_duplicate_keys(config_data, self.base_conf, True)
        assert not config.has_duplicate_keys(config_data, self.base_conf, False)

    def test_has_duplicate_keys_raises(self):
        config_data = dict(fear=123)
        assert_raises(
                errors.ConfigurationError,
                config.has_duplicate_keys,
                config_data,
                self.base_conf,
                True)

    def test_has_duplicate_keys_no_raise(self):
        config_data = dict(mind=123)
        assert config.has_duplicate_keys(config_data, self.base_conf, False)


class TestConfigurationWatcher(object):

    @pytest.yield_fixture(autouse=True)
    def setup_mocks_and_config_watcher(self):
        self.loader = mock.Mock()
        with mock.patch('staticconf.config.time') as self.mock_time:
            with mock.patch('staticconf.config.os.stat') as self.mock_stat:
                with tempfile.NamedTemporaryFile() as file:
                    with mock.patch('staticconf.config.os.path') as self.mock_path:
                        file.flush()
                        self.mock_stat.return_value.st_ino = 1
                        self.mock_stat.return_value.st_dev = 2
                        self.filename = file.name
                        self.watcher = config.ConfigurationWatcher(
                                self.loader, self.filename)
                        yield

    def test_get_filename_list_from_string(self):
        self.mock_path.abspath.side_effect = lambda p: p
        filename = 'thefilename.yaml'
        filenames = self.watcher.get_filename_list(filename)
        assert_equal(filenames, [filename])

    def test_get_filename_list_from_list(self):
        self.mock_path.abspath.side_effect = lambda p: p
        filenames = ['b', 'g', 'z', 'a']
        expected = ['a', 'b', 'g', 'z']
        assert_equal(self.watcher.get_filename_list(filenames), expected)

    def test_should_check(self):
        self.watcher.last_check = 123456789

        self.mock_time.time.return_value = 123456789
        # Still current, but no min_interval
        assert self.watcher.should_check

        # With max interval
        self.watcher.min_interval = 3
        assert not self.watcher.should_check

        # Time has passed
        self.mock_time.time.return_value = 123456794
        assert self.watcher.should_check

    def test_file_modified_not_modified(self):
        self.watcher.comparators[0].last_max_mtime = mtime = 222
        self.mock_path.getmtime.return_value = mtime
        self.mock_time.time.return_value = 123456
        assert not self.watcher.file_modified()
        assert_equal(self.watcher.last_check, self.mock_time.time.return_value)

    def test_file_modified(self):
        self.watcher.comparators[0].last_max_mtime = 123456
        self.mock_path.getmtime.return_value = 123460

        assert self.watcher.file_modified()
        assert_equal(self.watcher.last_check, self.mock_time.time.return_value)

    def test_reload_default(self):
        self.watcher.reload()
        self.loader.assert_called_with()

    def test_reload_custom(self):
        reloader = mock.Mock()
        watcher = config.ConfigurationWatcher(
                self.loader, self.filename, reloader=reloader)
        watcher.reload()
        reloader.assert_called_with()


class TestInodeComparator(object):

    def test_get_inodes_empty(self):
        comparator = config.InodeComparator([])
        assert comparator.get_inodes() == []

    @mock.patch('staticconf.config.os.stat', autospec=True)
    def test_get_inodes(self, mock_stat):
        comparator = config.InodeComparator(['./one.file'])
        inodes = comparator.get_inodes()
        expected = [(mock_stat.return_value.st_dev, mock_stat.return_value.st_ino)]
        assert_equal(inodes, expected)


class TestMTimeComparator(object):

    def test_get_most_recent_empty(self):
        comparator = config.MTimeComparator([])
        assert comparator.get_most_recent_changed() == -1

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, side_effect=[0,0,1,2,3])
    def test_get_most_recent(self, mock_mtime):
        comparator = config.MTimeComparator(['./one.file', './two.file'])
        assert comparator.get_most_recent_changed() == 2
        assert mock_mtime.call_count == 4

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, return_value=1)
    def test_no_change(self, mock_mtime):
        comparator = config.MTimeComparator(['./one.file'])
        assert not comparator.has_changed()
        assert not comparator.has_changed()

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, side_effect=[0,1,1,2])
    def test_changes(self, mock_mtime):
        comparator = config.MTimeComparator(['./one.file'])
        assert comparator.has_changed()
        assert not comparator.has_changed()
        assert comparator.has_changed()


class TestLoggingMTimeComparator(object):

    def __init__(self):
        self._LoggingMTimeComparator = functools.partial(config.MTimeComparator, err_logger=self._err_logger)

    @pytest.fixture(autouse=True)
    def _reset_err_logger(self):
        self._err_filename = None
        self._exc_info = (None, None, None)

    def _err_logger(self, filename):
        self._err_filename = filename
        self._exc_info = sys.exc_info()

    def test_logs_error(self):
        comparator = self._LoggingMTimeComparator(['./not.a.file'])
        assert comparator.get_most_recent_changed() == -1
        assert self._err_filename == "./not.a.file"
        assert all(x is not None for x in self._exc_info)

    def test_get_most_recent_empty(self):
        comparator = self._LoggingMTimeComparator([])
        assert comparator.get_most_recent_changed() == -1
        assert self._err_filename is None
        assert all(x is None for x in self._exc_info)

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, side_effect=[0,0,1,2,3])
    def test_get_most_recent(self, mock_mtime):
        comparator = self._LoggingMTimeComparator(['./one.file', './two.file'])
        assert comparator.get_most_recent_changed() == 2
        assert mock_mtime.call_count == 4
        assert self._err_filename is None
        assert all(x is None for x in self._exc_info)

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, return_value=1)
    def test_no_change(self, mock_mtime):
        comparator = self._LoggingMTimeComparator(['./one.file'])
        assert not comparator.has_changed()
        assert not comparator.has_changed()
        assert self._err_filename is None
        assert all(x is None for x in self._exc_info)

    @mock.patch('staticconf.config.os.path.getmtime', autospec=True, side_effect=[0,1,1,2])
    def test_changes(self, mock_mtime):
        comparator = self._LoggingMTimeComparator(['./one.file'])
        assert comparator.has_changed()
        assert not comparator.has_changed()
        assert comparator.has_changed()
        assert self._err_filename is None
        assert all(x is None for x in self._exc_info)


class TestMD5Comparator(object):

    @pytest.yield_fixture()
    def comparator(self):
        self.original_contents = b"abcdefghijkabcd"
        with tempfile.NamedTemporaryFile() as self.file:
            self.write_contents(self.original_contents)
            yield config.MD5Comparator([self.file.name])

    def write_contents(self, contents):
        self.file.seek(0)
        self.file.write(contents)
        self.file.flush()

    def test_get_hashes_empty(self):
        comparator = config.MD5Comparator([])
        assert comparator.get_hashes() == []

    def test_has_changed_no_changes(self, comparator):
        assert not comparator.has_changed()
        self.write_contents(self.original_contents)
        assert not comparator.has_changed()

    def test_has_changed_with_changes(self, comparator):
        assert not comparator.has_changed()
        self.write_contents(b"this is the new content")
        assert comparator.has_changed()


class TestReloadCallbackChain(object):

    @pytest.fixture(autouse=True)
    def setup_callback_chain(self):
        self.callbacks = list(enumerate([mock.Mock(), mock.Mock()]))
        self.callback_chain = config.ReloadCallbackChain(callbacks=self.callbacks)

    def test_init_with_callbacks(self):
        assert_equal(self.callback_chain.callbacks, dict(self.callbacks))

    def test_add_remove(self):
        callback = mock.Mock()
        self.callback_chain.add('one', callback)
        assert_equal(self.callback_chain.callbacks['one'], callback)
        self.callback_chain.remove('one')
        assert 'one' not in self.callback_chain.callbacks

    def test_call(self):
        self.callback_chain.namespace = 'the_namespace'
        with mock.patch('staticconf.config.reload') as mock_reload:
            self.callback_chain()
            for _, callback in self.callbacks:
                callback.assert_called_with()
                mock_reload.assert_called_with(name='the_namespace', all_names=False)


class TestConfigFacade(object):

    @pytest.fixture(autouse=True)
    def setup_facade(self):
        self.mock_watcher = mock.create_autospec(config.ConfigurationWatcher)
        self.mock_watcher.get_reloader.return_value = mock.create_autospec(
            config.ReloadCallbackChain)
        self.facade = config.ConfigFacade(self.mock_watcher)

    def test_load(self):
        filename, namespace = "filename", "namespace"
        loader = mock.Mock()

        with mock.patch(
                'staticconf.config.ConfigurationWatcher',
                autospec=True) as mock_watcher_class:
            facade = config.ConfigFacade.load(filename, namespace, loader)

        facade.watcher.load_config.assert_called_with()
        assert_equal(facade.watcher, mock_watcher_class.return_value)
        reloader = facade.callback_chain
        assert_equal(reloader, facade.watcher.get_reloader())

    def test_add_callback(self):
        name, func = 'name', mock.Mock()
        self.facade.add_callback(name, func)
        self.facade.callback_chain.add.assert_called_with(name, func)

    def test_reload_if_changed(self):
        self.facade.reload_if_changed()
        self.mock_watcher.reload_if_changed.assert_called_with(force=False)


@pytest.mark.acceptance
class TestConfigFacadeAcceptance(object):

    @pytest.fixture(autouse=True)
    def setup_env(self):
        self.file = tempfile.NamedTemporaryFile()
        self.write(b"one: A")

    def write(self, content, mtime_seconds=0):
        time.sleep(0.03)
        self.file.file.seek(0)
        self.file.write(content)
        self.file.flush()
        tstamp = time.time() + mtime_seconds
        os.utime(self.file.name, (tstamp, tstamp))

    @pytest.yield_fixture(autouse=True)
    def patch_namespace(self):
        self.namespace = 'testing_namespace'
        with testing.MockConfiguration(namespace=self.namespace):
            yield

    def test_load_end_to_end(self):
        loader = staticconf.YamlConfiguration
        callback = mock.Mock()
        facade = staticconf.ConfigFacade.load(self.file.name, self.namespace, loader)
        facade.add_callback('one', callback)
        assert_equal(staticconf.get('one', namespace=self.namespace), "A")

        self.write(b"one: B", 10)
        facade.reload_if_changed()
        assert_equal(staticconf.get('one', namespace=self.namespace), "B")
        callback.assert_called_with()

    def test_reload_end_to_end(self):
        loader = mock.Mock()
        callback = mock.Mock()
        facade = staticconf.ConfigFacade.load(
                self.file.name,
                self.namespace,
                loader)

        assert_equal(loader.call_count, 1)
        time.sleep(1)

        facade.reload_if_changed()
        assert_equal(loader.call_count, 1)
        os.utime(self.file.name, None)
        facade.reload_if_changed()
        assert_equal(loader.call_count, 2)


class TestBuildLoaderCallable(object):

    @pytest.yield_fixture(autouse=True)
    def patch_namespace(self):
        self.namespace = 'the_namespace'
        patcher = mock.patch('staticconf.config.get_namespace', autospec=True)
        with patcher as self.mock_get_namespace:
            yield

    def test_build_loader_callable(self):
        load_func, filename = mock.Mock(), mock.Mock()
        loader_callable = config.build_loader_callable(
                load_func, filename, self.namespace)
        result = loader_callable()
        self.mock_get_namespace.assert_called_with(self.namespace)
        mock_namespace = self.mock_get_namespace.return_value
        mock_namespace.clear.assert_called_with()
        load_func.assert_called_with(filename, namespace=self.namespace)
        assert_equal(result, load_func.return_value)
