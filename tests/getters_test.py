import mock
from testify import TestCase, assert_equal, run, setup_teardown
from testify.assertions import assert_in
from staticconf import getters, config, testing


class BuildGetterTestCase(TestCase):

    @setup_teardown
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


class NamespaceGettersTestCase(TestCase):

    @setup_teardown
    def teardown_proxies(self):
        self.namespace = 'the_test_namespace'
        with testing.MockConfiguration(namespace=self.namespace):
            yield

    def test_getters(self):
        get_conf = getters.NamespaceGetters(self.namespace)
        proxies = [
            get_conf.get_bool('is_it'),
            get_conf.get_time('when')
        ]

        namespace = config.get_namespace(get_conf.namespace)
        for proxy in proxies:
            assert_in(id(proxy), namespace.value_proxies)


if __name__ == "__main__":
    run()
