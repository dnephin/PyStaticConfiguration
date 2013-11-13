import logging

from testify import assert_equal, TestCase, run, assert_raises

import staticconf
from staticconf import testing, errors


class SomeClass(object):

    namespace = 'UniqueNamespaceForEndToEndTesting'
    alt_name  = 'UniqueNamespaceForEndToEndTestingAlternative'

    getters   = staticconf.NamespaceGetters(namespace)
    max       = getters.get_int('SomeClass.max')
    min       = getters.get_int('SomeClass.min')
    ratio     = getters.get_float('SomeClass.ratio')
    alt_ratio = getters.get_float('SomeClass.alt_ratio', 6.0)
    msg       = getters.get_string('SomeClass.msg', None)

    real_max  = staticconf.get_int('SomeClass.max', namespace=alt_name)
    real_min  = staticconf.get_int('SomeClass.min', namespace=alt_name)


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
        'options': ['1', '7', '3', '9'],
        'level': 'INFO',
    }

    def test_load_and_validate(self):
        staticconf.DictConfiguration(self.config, namespace=SomeClass.namespace)
        some_class = SomeClass()
        assert_equal(some_class.max, 100)
        assert_equal(some_class.min, 0)
        assert_equal(some_class.ratio, 7.7)
        assert_equal(some_class.alt_ratio, 6.0)
        assert_equal(SomeClass.getters.get('globals'), False)
        assert_equal(SomeClass.getters.get('enable'), 'True')
        assert_equal(SomeClass.getters.get_bool('enable'), True)
        assert_equal(some_class.msg, None)
        assert SomeClass.getters.get_regex('matcher').match('12345')
        assert not SomeClass.getters.get_regex('matcher').match('a')
        assert_equal(SomeClass.getters.get_list_of_int('options'), [1, 7, 3, 9])
        assert_equal(SomeClass.getters.get_log_level('level'), logging.INFO)

    def test_load_and_validate_namespace(self):
        real_config = {'SomeClass.min': 20, 'SomeClass.max': 25}
        staticconf.DictConfiguration(self.config, namespace=SomeClass.namespace)
        staticconf.DictConfiguration(real_config, namespace=SomeClass.alt_name)
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

    namespace = 'UniqueNamespaceForMockConfigurationTesting'
    getters = staticconf.NamespaceGetters(namespace)

    def test_mock_configuration_context_manager(self):
        one = self.getters.get('one')
        three = self.getters.get_int('three', default=3)

        with testing.MockConfiguration(dict(one=7), namespace=self.namespace):
            assert_equal(one, 7)
            assert_equal(three, 3)
        assert_raises(errors.ConfigurationError, self.getters.get('one'))

    def test_mock_configuration(self):
        two = self.getters.get_string('two')
        stars = self.getters.get_bool('stars')

        mock_config = testing.MockConfiguration(
            dict(two=2, stars=False), namespace=self.namespace)
        mock_config.setup()
        assert_equal(two, '2')
        assert not stars
        mock_config.teardown()
        assert_raises(errors.ConfigurationError, self.getters.get('two'))


if __name__ == "__main__":
    run()
