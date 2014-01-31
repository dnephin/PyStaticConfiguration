from testify import TestCase, assert_equal, run

import staticconf
from staticconf import testing


class MockConfigurationTestCase(TestCase):

    def test_init(self):
        with testing.MockConfiguration(a='one', b='two'):
            assert_equal(staticconf.get('a'), 'one')
            assert_equal(staticconf.get('b'), 'two')

    def test_init_nested(self):
        conf = {
            'a': {
                'b': 'two',
            },
            'c': 'three'
        }
        with testing.MockConfiguration(conf):
            assert_equal(staticconf.get('a.b'), 'two')
            assert_equal(staticconf.get('c'), 'three')

if __name__ == "__main__":
    run()
