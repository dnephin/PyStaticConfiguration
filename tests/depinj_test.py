
from testify import TestCase, setup_teardown
from testify.assertions import assert_equal, assert_is, assert_is_not
from testify.assertions import assert_raises_and_contains

from staticconf import testing, depinj


class FirstDep(object):

    def name(self):
        return 'FirstDep'


class SecondDep(object):

    def __init__(self, dep, thing='on'):
        self.dep = dep
        self.thing = thing

    def name(self):
        return 'SecondDep %s' % self.thing

    def run(self):
        return self.dep.name()



class DependencyInjectionAcceptanceTest(TestCase):

    @setup_teardown
    def patch_namespace(self):
        with testing.MockConfiguration(namespace=depinj.name):
            depinj.register('First', FirstDep)
            depinj.register('Second',
                            SecondDep, depinj.use('First'), thing='off')
            yield

    def test_use_dependencies(self):
        second = depinj.use('Second')
        other = depinj.use('First')

        assert_equal(second.name(), 'SecondDep off')
        assert_equal(second.run(), 'FirstDep')
        assert_is(second.value, second.value)
        assert_is_not(other.value, second.dep.value)

    def test_register_single(self):
        depinj.register_single('Foo', FirstDep)
        assert_is(depinj.use('Foo').value, depinj.use('Foo').value)

    def test_unknwon_dependency(self):
        dep_name = 'this_thing'
        assert_raises_and_contains(
            depinj.UnknownDependency,
            dep_name,
            depinj.use(dep_name))
