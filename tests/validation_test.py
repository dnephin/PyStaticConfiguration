import datetime
from testify import assert_equal, run, TestCase
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

    def test_validate_datetime_already_datetime(self):
        expected = datetime.datetime(2012, 3, 14, 18, 5, 5)
        actual = validation.validate_datetime(expected)
        assert_equal(actual, expected)

    def test_validate_date(self):
        actual = validation.validate_date("03/14/12")
        expected = datetime.date(2012, 3, 14)
        assert_equal(actual, expected)

    def test_validate_date_already_date(self):
        expected = datetime.date(2012, 3, 14)
        actual = validation.validate_date(expected)
        assert_equal(actual, expected)

    def test_validate_time(self):
        actual = validation.validate_time("4:12:14")
        expected = datetime.time(4, 12, 14)
        assert_equal(actual, expected)

    def test_validate_time_pm_format(self):
        actual = validation.validate_time("4:12:14 pm")
        expected = datetime.time(16, 12, 14)
        assert_equal(actual, expected)

    def test_validate_time_already_time(self):
        expected = datetime.time(16, 12, 14)
        actual = validation.validate_time(expected)
        assert_equal(actual, expected)


class IterableValidationTestCase(TestCase):

    def test_validate_list(self):
        expected = range(3)
        actual = validation.validate_list((0, 1, 2))
        assert_equal(expected, actual)

    def test_validate_set(self):
        expected = set([3, 2, 1])
        actual = validation.validate_set([1,3,2,2,1,3,2])
        assert_equal(expected, actual)

if __name__ == "__main__":
    run()