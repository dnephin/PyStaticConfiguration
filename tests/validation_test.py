import datetime
import logging

from staticconf import validation, errors
from testing.testifycompat import (
    assert_equal,
    assert_raises_and_contains,
)


class TestValidation(object):

    def test_validate_string(self):
        assert_equal(None, validation.validate_string(None))
        assert_equal('asd', validation.validate_string('asd'))
        assert_equal('123', validation.validate_string(123))


class TestDateTimeValidation(object):

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


class TestIterableValidation(object):

    def test_validate_list(self):
        expected = range(3)
        actual = validation.validate_list((0, 1, 2))
        assert_equal(expected, actual)

    def test_validate_set(self):
        expected = set([3, 2, 1])
        actual = validation.validate_set([1, 3, 2, 2, 1, 3, 2])
        assert_equal(expected, actual)


class TestRegexValidation(object):

    def test_validate_regex_success(self):
        pattern = '^(:?what)\s+could\s+go\s+(wrong)[!?.,]$'
        actual = validation.validate_regex(pattern)
        assert_equal(pattern, actual.pattern)

    def test_validate_regex_failed(self):
        pattern = "((this) regex is broken"
        assert_raises_and_contains(
                errors.ValidationError,
                pattern,
                validation.validate_regex,
                pattern)

    def test_validate_regex_none(self):
        assert_raises_and_contains(
                errors.ValidationError,
                'None',
                validation.validate_regex,
                None)


class TestBuildListOfTypeValidator(object):

    def test_build_list_of_type_ints_success(self):
        validator = validation.build_list_type_validator(
            validation.validate_int)
        expected = range(3)
        assert_equal(validator(['0', '1', '2']), expected)

    def test_build_list_of_type_float_failed(self):
        validator = validation.build_list_type_validator(
            validation.validate_float)
        assert_raises_and_contains(
            errors.ValidationError, 'Invalid float: a', validator, ['0.1', 'a'])

    def test_build_list_of_type_empty_list(self):
        validator = validation.build_list_type_validator(
            validation.validate_string)
        assert_equal(validator([]), [])

    def test_build_list_of_type_not_a_list(self):
        validator = validation.build_list_type_validator(
            validation.validate_any)
        assert_raises_and_contains(
            errors.ValidationError, 'Invalid iterable', validator, None)


class TestBuildMappingTypeValidator(object):

    def test_build_map_from_list_of_pairs(self):
        pair_validator = validation.build_map_type_validator(lambda i: i)
        expected = {0: 0, 1: 1, 2: 2}
        assert_equal(pair_validator(enumerate(range(3))), expected)

    def test_build_map_from_list_of_dicts(self):
        map_by_id = lambda d: (d['id'], d['value'])
        map_validator = validation.build_map_type_validator(map_by_id)
        expected = {'a': 'b', 'c': 'd'}
        source = [dict(id='a', value='b'), dict(id='c', value='d')]
        assert_equal(map_validator(source), expected)


class TestValidateLogLevel(object):

    def test_valid_log_level(self):
        assert_equal(validation.validate_log_level('WARN'), logging.WARN)
        assert_equal(validation.validate_log_level('DEBUG'), logging.DEBUG)

    def test_invalid_log_level(self):
        assert_raises_and_contains(
                errors.ValidationError,
                'UNKNOWN',
                validation.validate_log_level,
                'UNKNOWN')
