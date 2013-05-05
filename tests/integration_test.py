from testify import assert_equal, TestCase, run, teardown, assert_raises

import staticconf
from staticconf import config, testing, errors


class SomeClass(object):

    max = staticconf.get_int('SomeClass.max')
    min = staticconf.get_int('SomeClass.min')
    ratio = staticconf.get_float('SomeClass.ratio')
    alt_ratio = staticconf.get_float('SomeClass.alt_ratio', 6.0)
    msg = staticconf.get_string('SomeClass.msg', None)

    real_max = staticconf.get_int('SomeClass.max', namespace='real')
    real_min = staticconf.get_int('SomeClass.min', namespace='real')


class EndToEndTestCase(TestCase):

    config = {
        'SomeClass': {
            'max': 100,
            'min': '0',
            'ratio': '7.7'
        },
        'globals': False,
        'enable': 'True',
        'matcher': '\d+',
        'options': ['1', '7', '3', '9']
    }

    @teardown
    def teardown_configs(self):
        config._reset()

    def test_load_and_validate(self):
        staticconf.DictConfiguration(self.config)
        some_class = SomeClass()
        assert_equal(some_class.max, 100)
        assert_equal(some_class.min, 0)
        assert_equal(some_class.ratio, 7.7)
        assert_equal(some_class.alt_ratio, 6.0)
        assert_equal(staticconf.get('globals'), False)
        assert_equal(staticconf.get('enable'), 'True')
        assert_equal(staticconf.get_bool('enable'), True)
        assert_equal(some_class.msg, None)
        assert staticconf.get_regex('matcher').match('12345')
        assert not staticconf.get_regex('matcher').match('a')
        assert_equal(staticconf.get_list_of_int('options'), [1, 7, 3, 9])

    def test_load_and_validate_namespace(self):
        real_config = {'SomeClass.min': 20, 'SomeClass.max': 25}
        staticconf.DictConfiguration(self.config)
        staticconf.DictConfiguration(real_config, namespace='real')
        some_class = SomeClass()
        assert_equal(some_class.max, 100)
        assert_equal(some_class.min, 0)
        assert_equal(some_class.real_min, 20)
        assert_equal(some_class.real_max, 25)

    def test_readers(self):
        staticconf.DictConfiguration(self.config)
        assert_equal(staticconf.read_float('SomeClass.ratio'), 7.7)
        assert_equal(staticconf.read_bool('globals'), False)
        assert_equal(staticconf.read_list_of_int('options'), [1, 7, 3, 9])


class MockConfigurationTestCase(TestCase):

    def test_mock_configuration_context_manager(self):
        one = staticconf.get('one')
        three = staticconf.get_int('three', default=3)

        with testing.MockConfiguration(dict(one=7)):
            assert_equal(one, 7)
            assert_equal(three, 3)
        assert_raises(errors.ConfigurationError, staticconf.get('one'))

    def test_mock_configuration(self):
        two = staticconf.get_string('two')
        stars = staticconf.get_bool('stars')

        mock_config = testing.MockConfiguration(dict(two=2, stars=False))
        mock_config.setup()
        assert_equal(two, '2')
        assert not stars
        mock_config.teardown()
        assert_raises(errors.ConfigurationError, staticconf.get('two'))


if __name__ == "__main__":
    run()
