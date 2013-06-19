import datetime
from testify import assert_equal, run, TestCase, setup
from testify.assertions import assert_raises_and_contains
from staticconf import validation, errors


class ValidationTestCase(TestCase):

    def test_validate_string(self):
        assert_equal(None, validation.validate_string(None))
        assert_equal('asd', validation.validate_string('asd'))
        assert_equal('123', validation.validate_string(123))


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


class RegexValidationTestCase(TestCase):

    def test_validate_regex_success(self):
        pattern = '^(:?what)\s+could\s+go\s+(wrong)[!?.,]$'
        actual = validation.validate_regex(pattern)
        assert_equal(pattern, actual.pattern)

    def test_validate_regex_failed(self):
        pattern = "((this) regex is broken"
        assert_raises_and_contains(errors.ValidationError, pattern,
            validation.validate_regex, pattern)

    def test_validate_regex_none(self):
        assert_raises_and_contains(errors.ValidationError, 'None',
            validation.validate_regex, None)


class BuildListOfTypeValidatorTestCase(TestCase):

    def test_build_list_of_type_ints_success(self):
        validator = validation.build_list_type_validator(
            validation.validate_int)
        expected = range(3)
        assert_equal(validator(['0', '1','2']), expected)

    def test_build_list_of_type_float_failed(self):
        validator = validation.build_list_type_validator(
            validation.validate_float)
        assert_raises_and_contains(
            errors.ValidationError, 'invalid float: a', validator, ['0.1', 'a'])

    def test_build_list_of_type_empty_list(self):
        validator = validation.build_list_type_validator(
            validation.validate_string)
        assert_equal(validator([]), [])

    def test_build_list_of_type_not_a_list(self):
        validator = validation.build_list_type_validator(
            validation.validate_any)
        assert_raises_and_contains(
            errors.ValidationError, 'invalid iterable', validator, None)


class BuildMappingTypeValidatorTestCase(TestCase):

    @setup
    def setup_validator(self):
        self.pair_validator = validation.build_map_type_validator(lambda i: i)
        map_by_id = lambda d: (d['id'], d['value'])
        self.map_validator = validation.build_map_type_validator(map_by_id)

    def test_build_map_from_list_of_pairs(self):
        expected = {0: 0, 1: 1, 2:2}
        assert_equal(self.pair_validator(enumerate(range(3))), expected)

    def test_build_map_from_list_of_dicts(self):
        expected = {'a': 'b', 'c': 'd'}
        source = [dict(id='a', value='b'), dict(id='c', value='d')]
        assert_equal(self.map_validator(source), expected)


if __name__ == "__main__":
    run()
