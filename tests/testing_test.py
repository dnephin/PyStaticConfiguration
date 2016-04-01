
import staticconf
from staticconf import testing

from testing.testifycompat import assert_equal


class TestMockConfiguration(object):

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


class TestPatchConfiguration(object):

    def test_nested(self):
        with testing.MockConfiguration(a='one', b='two'):
            with testing.PatchConfiguration(a='three'):
                assert_equal(staticconf.get('a'), 'three')
                assert_equal(staticconf.get('b'), 'two')

            assert_equal(staticconf.get('a'), 'one')
            assert_equal(staticconf.get('b'), 'two')

    def test_not_nested(self):
        with testing.PatchConfiguration(a='one', b='two'):
            assert_equal(staticconf.get('a'), 'one')
            assert_equal(staticconf.get('b'), 'two')
