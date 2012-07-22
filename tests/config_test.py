import mock
from testify import run, assert_equal, TestCase, setup
from testify.assertions import assert_raises

from staticconf import proxy


class BuildGetterTestCase(TestCase):

    def test_build_getter(self):
        validator = mock.Mock()