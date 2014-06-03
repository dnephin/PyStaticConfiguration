import datetime

import mock
import pytest

from testing.testifycompat import (
    assert_equal,
    assert_raises_and_contains,
    assert_in,
)
from staticconf import proxy, validation, errors, config


class TestExtractValue(object):

    @pytest.fixture(autouse=True)
    def setup_configuration_values(self):
        validator = mock.Mock(return_value=2)
        self.name = 'test_namespace'
        self.namespace = config.get_namespace(self.name)
        self.config_key = 'something'
        self.value_proxy = proxy.ValueProxy(
            validator, self.namespace, self.config_key)

    def test_extract_value_unset(self):
        expected = [self.name, self.config_key]
        assert_raises_and_contains(
                errors.ConfigurationError,
                expected,
                lambda: self.value_proxy.value)

    def test_get_value_fails_validation(self):
        expected = [self.name, self.config_key]
        validator = mock.Mock(side_effect=validation.ValidationError)
        _ = proxy.ValueProxy(  # flake8: noqa
                validator,
                self.namespace,
                'something.broken')
        assert_raises_and_contains(
                errors.ConfigurationError,
                expected,
                lambda: self.value_proxy.value)


class TestValueProxy(object):

    @pytest.fixture(autouse=True)
    def setup_configuration_values(self):
        self.value_cache = {
            'something': 2,
            'something.string': 'the stars',
            'zero': 0,
            'the_date': datetime.datetime(2012, 3, 14, 4, 4, 4),
            'the_list': range(3),
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
        assert_equal(3 ** value_proxy, 9)
        assert_equal(value_proxy ** 3, 8)
        assert_equal(hash(value_proxy), 2)
        assert_equal(abs(value_proxy), 2)
        assert_equal(hex(value_proxy), "0x2")
        assert bool(value_proxy)
        assert_equal(range(5)[value_proxy], 2)
        assert_equal(range(5)[:value_proxy], [0, 1])

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
        assert_equal(hash(value_proxy), hash("one%s"))
        assert bool(value_proxy)

    def test_proxy_with_datetime(self):
        the_date = datetime.datetime(2012, 12, 1, 5, 5, 5)
        validator = mock.Mock(return_value=the_date)
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'something')
        assert_equal(value_proxy, the_date)
        assert value_proxy < datetime.datetime(2012, 12, 3)
        assert value_proxy > datetime.datetime(2012, 1, 4)
        four_days_ahead = datetime.datetime(2012, 12, 4, 5, 5, 5)
        assert_equal(value_proxy + datetime.timedelta(days=3), four_days_ahead)
        assert_equal(repr(value_proxy), repr(the_date))
        assert_equal(str(value_proxy), str(the_date))
        assert_equal(hash(value_proxy), hash(the_date))
        assert bool(value_proxy)

    def test_proxy_zero(self):
        validator = mock.Mock(return_value=0)
        self.value_proxy = proxy.ValueProxy(validator, self.value_cache, 'zero')
        assert_equal(self.value_proxy, 0)
        assert not self.value_proxy
        assert not self.value_proxy and True
        assert not self.value_proxy or False
        assert not self.value_proxy ^ 0
        assert ~ self.value_proxy

    def test_get_value(self):
        expected = "the stars"
        validator = mock.Mock(return_value=expected)
        value_proxy = proxy.ValueProxy(
            validator, self.value_cache, 'something.string')
        assert_equal(value_proxy, expected)

    def test_get_value_cached(self):
        expected = "the other stars"
        validator = mock.Mock()
        value_proxy = proxy.ValueProxy(
            validator, self.value_cache, 'something.string')
        value_proxy._value = expected
        assert_equal(value_proxy.value, expected)
        validator.assert_not_called()

    def test_proxied_attributes(self):
        validator = mock.Mock(return_value=self.value_cache['the_date'])
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'the_date')
        assert_equal(value_proxy.date(), datetime.date(2012, 3, 14))
        assert_equal(value_proxy.hour, 4)

    def test_proxy_list(self):
        the_list = range(3)
        validator = mock.Mock(return_value=the_list)
        value_proxy = proxy.ValueProxy(validator, self.value_cache, 'the_list')
        assert_equal(value_proxy, the_list)
        assert_in(2, value_proxy)
        assert_equal(value_proxy[:1], [0])
        assert_equal(len(value_proxy), 3)
