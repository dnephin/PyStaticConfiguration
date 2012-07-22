import datetime
from testify import assert_equal, run, setup, TestCase
from staticconf import validation


class DateTimeValidationTestCase(TestCase):

    def test_validate_datetime(self):
        actual = validation.validate_datetime("2012-03-14 05:05:05")
        expected = datetime.datetime(2012, 3, 14, 5, 5, 5)
        assert_equal(actual, expected)

    def test_validate_datetime_pm_format(self):
        actual = validation.validate_datetime("2012-03-14 6:05:05 PM")
        expected = datetime.datetime(2012, 3, 14, 18, 5, 5)
        assert_equal(actual, expected)

    def test_validate_date(self):
        actual = validation.validate_date("03/14/12")
        expected = datetime.date(2012, 3, 14)
        assert_equal(actual, expected)

    def test_validate_time(self):
        actual = validation.validate_time("4:12:14")
        expected = datetime.time(4, 12, 14)
        assert_equal(actual, expected)

    def test_validate_time_pm_format(self):
        actual = validation.validate_time("4:12:14 pm")
        expected = datetime.time(16, 12, 14)
        assert_equal(actual, expected)