"""Compatiblity functions for py.test to migrate code from testify.
"""
from unittest import mock  # noqa

import pytest


def assert_equal(left, right):
    assert left == right


def assert_raises_and_contains(exc, text, func, *args, **kwargs):
    with pytest.raises(exc) as excinfo:
        func(*args, **kwargs)

    assert exc == excinfo.type
    text = text if isinstance(text, list) else [text]
    for item in text:
        assert item in str(excinfo.exconly())


def assert_raises(exc, func, *args, **kwargs):
    with pytest.raises(exc) as excinfo:
        func(*args, **kwargs)
    assert exc == excinfo.type


def assert_in(item, container):
    assert item in container


def assert_not_in(item, container):
    assert item not in container


def assert_is(left, right):
    assert left is right
