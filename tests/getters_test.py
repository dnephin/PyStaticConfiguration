import mock
from testify import TestCase, assert_equal, run, teardown
from staticconf import getters, config

class BuildGetterTestCase(TestCase):

    @teardown
    def teardown_proxies(self):
        config._reset()

    def test_build_getter(self):
        validator = mock.Mock()
        getter = getters.build_getter(validator)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(config.DEFAULT)
        assert value_proxy is namespace.get_value_proxies()[-1]
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, namespace.configuration_values)

    def test_build_getter_with_getter_namespace(self):
        validator = mock.Mock()
        name = 'the stars'
        getter = getters.build_getter(validator, getter_namespace=name)
        assert callable(getter), "Getter is not callable"
        value_proxy = getter('the_name')
        namespace = config.get_namespace(name)
        assert value_proxy is namespace.get_value_proxies()[-1]
        assert_equal(value_proxy.config_key, "the_name")
        assert_equal(value_proxy.value_cache, namespace.configuration_values)


class NamespaceGettersTestCase(TestCase):

    @teardown
    def teardown_proxies(self):
        config._reset()

    def test_getters(self):
        get_conf = getters.NamespaceGetters('the_space')
        proxies = [
            get_conf.get_bool('is_it'),
            get_conf.get_time('when')
        ]

        namespace = config.get_namespace(get_conf.namespace)
        for i in xrange(len(proxies)):
            assert proxies[i] is namespace.value_proxies[i]


if __name__ == "__main__":
    run()
