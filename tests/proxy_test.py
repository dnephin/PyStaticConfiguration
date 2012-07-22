import mock
from testify import run, assert_equal, TestCase, setup
from testify.assertions import assert_raises

from staticconf import proxy, validation, errors


class ValueProxyTestCase(TestCase):

    @setup
    def setup_configuration_values(self):
        self.value_cache = {
            'something': 2,
            'something.string': 'the stars',
            'zero': 0
        }

    def test_proxy(self):
        validator = mock.Mock(return_value=2)
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something')
        assert_equal(value_proxy, 2)
        assert value_proxy < 4
        assert value_proxy > 1
        assert_equal(value_proxy + 5, 7)
        assert_equal(repr(value_proxy), "2")
        assert_equal(str(value_proxy), "2")
        assert bool(value_proxy)

    def test_proxy_zero(self):
        validator = mock.Mock(return_value=0)
        self.value_proxy = proxy.ValueProxy(validator, self.value_cache, 'zero')
        assert_equal(self.value_proxy, 0)
        assert not bool(self.value_proxy)

    def test_get_value(self):
        expected = "the stars"
        validator = mock.Mock(return_value=expected)
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.string')
        value = value_proxy.get_value()
        assert_equal(value, expected)

    def test_get_value_cached(self):
        expected = "the other stars"
        validator = mock.Mock()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.string')
        value_proxy.value =  expected
        value = value_proxy.get_value()
        assert_equal(value, expected)
        validator.assert_not_called()

    def test_get_value_unset(self):
        validator = mock.Mock()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.missing')
        assert_raises(errors.ConfigurationError, value_proxy.get_value)

    def test_get_value_fails_validation(self):
        validator = mock.Mock()
        validator.side_effect = validation.ValidationError()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.broken')
        assert_raises(errors.ConfigurationError, value_proxy.get_value)


if __name__ == "__main__":
    run()
