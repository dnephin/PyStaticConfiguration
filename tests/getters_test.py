import pytest

from testing.testifycompat import (
    assert_equal,
    assert_in,
    assert_is,
    mock,
)
from staticconf import getters, config, testing


class TestBuildGetter:

    @pytest.yield_fixture(autouse=True)
    def teardown_proxies(self):
        with testing.MockConfiguration():
            yield

    def test_build_getter(self):
        validator = mock.Mock()
        getter = getters.build_getter(validator)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(config.DEFAULT)
        assert_in(id(value_proxy), namespace.value_proxies)
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.namespace, namespace)

    def test_build_getter_with_getter_namespace(self):
        validator = mock.Mock()
        name = 'the stars'
        getter = getters.build_getter(validator, getter_namespace=name)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(name)
        assert_in(id(value_proxy), namespace.value_proxies)
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.namespace, namespace)


class TestNamespaceGetters:

    @pytest.yield_fixture(autouse=True)
    def teardown_proxies(self):
        self.namespace = 'the_test_namespace'
        with testing.MockConfiguration(namespace=self.namespace):
            yield

    def test_getters(self):
        get_conf = getters.NamespaceGetters(self.namespace)
        proxies = [
            get_conf.get_bool('is_it'),
            get_conf.get_time('when'),
            get_conf.get_list_of_bool('options')
        ]

        namespace = config.get_namespace(get_conf.namespace)
        for proxy in proxies:
            assert_in(id(proxy), namespace.value_proxies)


class TestProxyFactory:

    @pytest.yield_fixture(autouse=True)
    def patch_registries(self):
        patcher = mock.patch('staticconf.getters.register_value_proxy')
        with patcher as self.mock_register:
            yield

    @pytest.fixture(autouse=True)
    def setup_factory(self):
        self.factory = getters.ProxyFactory()
        self.validator = mock.Mock()
        self.namespace = mock.create_autospec(config.ConfigNamespace)
        self.config_key = 'some_key'
        self.default = 'bad_default'
        self.help = 'some help message no one reads'
        self.args = (
            self.validator,
            self.namespace,
            self.config_key,
            self.default,
            self.help)

    def test_build_new(self):
        value_proxy = self.factory.build(*self.args)
        self.mock_register.assert_called_with(
            self.namespace, value_proxy, self.help)

    def test_build_existing(self):
        value_proxy = self.factory.build(*self.args)
        self.mock_register.reset_mock()

        assert_is(value_proxy, self.factory.build(*self.args))
        assert not self.mock_register.mock_calls

    def test_build_with_immutable_default(self):
        args = self.validator, self.namespace, self.config_key, [], self.help
        self.factory.build(*args)
        assert_in(repr(args[:-1]), self.factory.proxies)
