import datetime
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
            'zero': 0,
            'the_date': datetime.datetime(2012, 3, 14, 4, 4, 4)
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
        assert_equal(3 % value_proxy, 1)
        assert_equal(3 ** 2, 9)
        assert bool(value_proxy)

    def test_proxy_with_string(self):
        validator = mock.Mock(return_value='one%s')
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something')
        assert_equal(value_proxy, 'one%s')
        assert value_proxy < 'two'
        assert value_proxy > 'ab'
        assert_equal(value_proxy + '!', 'one%s!')
        assert_equal(value_proxy % '!', 'one!')
        assert_equal(repr(value_proxy), "'one%s'")
        assert_equal(str(value_proxy), "one%s")
        assert bool(value_proxy)

    def test_proxy_with_datetime(self):
        the_date = datetime.datetime(2012, 12, 1, 5, 5, 5)
        validator = mock.Mock(return_value=the_date)
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something')
        assert_equal(value_proxy, the_date)
        assert value_proxy < datetime.datetime(2012, 12, 3)
        assert value_proxy > datetime.datetime(2012, 1, 4)
        four_days_ahead = datetime.datetime(2012, 12, 4 ,5, 5, 5)
        assert_equal(value_proxy + datetime.timedelta(days=3), four_days_ahead)
        assert_equal(repr(value_proxy), repr(the_date))
        assert_equal(str(value_proxy), str(the_date))
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
        assert_equal(value_proxy, expected)

    def test_get_value_cached(self):
        expected = "the other stars"
        validator = mock.Mock()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.string')
        value_proxy._value =  expected
        assert_equal(value_proxy.value, expected)
        validator.assert_not_called()

    def test_get_value_unset(self):
        validator = mock.Mock()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.missing')
        assert_raises(errors.ConfigurationError, lambda: value_proxy + 1)

    def test_get_value_fails_validation(self):
        validator = mock.Mock()
        validator.side_effect = validation.ValidationError()
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something.broken')
        assert_raises(errors.ConfigurationError, lambda: value_proxy + 1)

    def test_proxied_attributes(self):
        validator = mock.Mock(return_value=self.value_cache['the_date'])
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'the_date')
        assert_equal(value_proxy.date(), datetime.date(2012, 3, 14))
        assert_equal(value_proxy.hour, 4)

if __name__ == "__main__":
    run()
