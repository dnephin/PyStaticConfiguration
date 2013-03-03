import contextlib
import mock
from testify import TestCase, assert_equal, setup_teardown, setup
from testify.assertions import assert_raises
from staticconf import testing, schema, validation, config, errors


class CreateValueTypeTestCase(TestCase):

    def test_create_value_type(self):
        namespace = mock.create_autospec(config.ConfigNamespace)
        namespace.get.return_value = 7
        float_type = schema.create_value_type(validation.validate_float)
        assert callable(float_type)
        value_token = float_type(default=5, config_key='one')
        value_token.set_namespace(namespace)
        assert_equal(value_token.get_value(), 7)


class TestingSchema(object):
    __metaclass__ = schema.SchemaMeta

    namespace = 'my_testing_namespace'

    one = schema.Int(default=5)
    two = schema.String(help='the value for two')
    some_value = schema.String(config_key='three.four')


class SchemaMetaTestCase(TestCase):

    @setup_teardown
    def mock_config(self):
        with contextlib.nested(
            mock.patch('staticconf.schema.config', autospec=True),
            mock.patch('staticconf.schema.getters', autospec=True)
        ) as (self.mock_config, self.mock_getters):
            self.scheme_object = TestingSchema()
            self.meta = self.scheme_object.__class__
            yield

    def test_get_namespace_missing(self):
        assert_raises(errors.ConfigurationError, self.meta.get_namespace, {})

    def test_get_namespace_present(self):
        name = 'the_namespace'
        namespace = self.meta.get_namespace({'namespace': name})
        self.mock_config.get_namespace.assert_called_with(name)
        assert_equal(namespace, self.mock_config.get_namespace.return_value)

    def test_build_attributes(self):
        token = mock.create_autospec(schema.ValueToken)
        attributes = {
            'not_a_token': None,
            'a_token': token
        }
        namespace = mock.create_autospec(config.ConfigNamespace)
        attributes = self.meta.build_attributes(attributes, namespace)
        assert_equal(attributes['not_a_token'], None)
        assert_equal(attributes['_tokens'], {'a_token': token})
        token.set_namespace.assert_called_with(namespace)
        token.set_default_config_key.assert_called_with('a_token')
        assert isinstance(attributes['a_token'], property)
        self.mock_getters.register_value_proxy.assert_called_with(
            namespace, token, token.help)


class SchemaAcceptanceTestCase(TestCase):

    @setup_teardown
    def setup_config(self):
        conf = {
            'one': '1',
            'two': 'another',
            'three.four': 'deeper'
        }
        with testing.MockConfiguration(conf, namespace=TestingSchema.namespace):
            yield

    def test_schema(self):
        config_schema = TestingSchema()
        assert_equal(config_schema.some_value, 'deeper')
        assert_equal(config_schema.one, 1)
        assert_equal(config_schema.two, 'another')
