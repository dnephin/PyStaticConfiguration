import contextlib
import mock
from testify import TestCase, assert_equal, setup_teardown
from testify.assertions import assert_raises
from staticconf import testing, schema, validation, config, errors


class CreateValueTypeTestCase(TestCase):

    def test_build_value_type(self):
        help_text = 'what?'
        config_key = 'one'
        float_type = schema.build_value_type(validation.validate_float)
        assert callable(float_type)
        value_def = float_type(default=5, config_key=config_key, help=help_text)
        assert_equal(value_def.default, 5)
        assert_equal(value_def.help, help_text)
        assert_equal(value_def.config_key, config_key)


class TestingSchema(object):
    __metaclass__ = schema.SchemaMeta

    namespace = 'my_testing_namespace'

    config_path = 'my.thing'

    one = schema.int(default=5)
    two = schema.string(help='the value for two')
    some_value = schema.any(config_key='three.four')
    when = schema.date()
    really_when = schema.datetime()
    at_time = schema.time()
    really = schema.bool()
    ratio = schema.float()
    all_of_them = schema.list()
    some_of_them = schema.set()
    wrapped = schema.tuple()
    options = schema.list_of_bool()


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
        value_def = mock.create_autospec(schema.ValueTypeDefinition)
        attributes = {
            'not_a_token': None,
            'a_token': value_def
        }
        namespace = mock.create_autospec(config.ConfigNamespace)
        attributes = self.meta.build_attributes(attributes, namespace)
        assert_equal(attributes['not_a_token'], None)
        assert_equal(attributes['_tokens'].keys(), ['a_token'])
        token = attributes['_tokens']['a_token']
        assert_equal(token.config_key, value_def.config_key)
        assert_equal(token.default, value_def.default)
        assert isinstance(attributes['a_token'], property)
        self.mock_getters.register_value_proxy.assert_called_with(
            namespace, token, value_def.help)


class SchemaAcceptanceTestCase(TestCase):

    @setup_teardown
    def setup_config(self):
        conf = {
            'my.thing.one': '1',
            'my.thing.two': 'another',
            'my.thing.three.four': 'deeper'
        }
        with testing.MockConfiguration(conf, namespace=TestingSchema.namespace):
            yield

    def test_schema(self):
        config_schema = TestingSchema()
        assert_equal(config_schema.some_value, 'deeper')
        assert_equal(config_schema.one, 1)
        assert_equal(config_schema.two, 'another')
