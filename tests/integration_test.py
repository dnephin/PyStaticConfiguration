from testify import assert_equal, TestCase, run, teardown

import staticconf
from staticconf import config


class SomeClass(object):

    max = staticconf.get_int('SomeClass.max')
    min = staticconf.get_int('SomeClass.min')
    ratio = staticconf.get_float('SomeClass.ratio')
    alt_ratio = staticconf.get_float('SomeClass.alt_ratio', 6.0)


class EndToEndTestCase(TestCase):

    config = {
        'SomeClass': {
            'max': 100,
            'min': '0',
            'ratio': '7.7'
        },
        'globals': False,
        'enable': 'True'
    }

    @teardown
    def teardown_configs(self):
        config.reset()

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


if __name__ == "__main__":
    run()