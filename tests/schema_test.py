import pytest

from testing.testifycompat import (
    assert_equal,
    assert_raises,
    mock,
)
from staticconf import testing, schema, validation, config, errors


class TestCreateValueType:

    def test_build_value_type(self):
        help_text = 'what?'
        config_key = 'one'
        float_type = schema.build_value_type(validation.validate_float)
        assert callable(float_type)
        value_def = float_type(default=5, config_key=config_key, help=help_text)
        assert_equal(value_def.default, 5)
        assert_equal(value_def.help, help_text)
        assert_equal(value_def.config_key, config_key)


class ATestingSchema(metaclass=schema.SchemaMeta):

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


@pytest.yield_fixture
def meta_schema():
    with mock.patch('staticconf.schema.config', autospec=True) as mock_config:
        with mock.patch('staticconf.schema.getters',
                        autospec=True) as mock_getters:
            schema_object = ATestingSchema()
            yield schema_object.__class__, mock_config, mock_getters


class TestSchemaMeta:

    def test_get_namespace_missing(self, meta_schema):
        meta, _, _ = meta_schema
        assert_raises(errors.ConfigurationError, meta.get_namespace, {})

    def test_get_namespace_present(self, meta_schema):
        meta, mock_config, _ = meta_schema
        name = 'the_namespace'
        namespace = meta.get_namespace({'namespace': name})
        mock_config.get_namespace.assert_called_with(name)
        assert_equal(namespace, mock_config.get_namespace.return_value)

    def test_build_attributes(self, meta_schema):
        meta, _, mock_getters = meta_schema
        value_def = mock.create_autospec(schema.ValueTypeDefinition)
        attributes = {
            'not_a_token': None,
            'a_token': value_def
        }
        namespace = mock.create_autospec(config.ConfigNamespace)
        attributes = meta.build_attributes(attributes, namespace)
        assert_equal(attributes['not_a_token'], None)
        assert_equal(list(attributes['_tokens'].keys()), ['a_token'])
        token = attributes['_tokens']['a_token']
        assert_equal(token.config_key, value_def.config_key)
        assert_equal(token.default, value_def.default)
        assert isinstance(attributes['a_token'], property)
        mock_getters.register_value_proxy.assert_called_with(
            namespace, token, value_def.help)


@pytest.yield_fixture
def testing_schema_namespace():
    conf = {
        'my.thing.one': '1',
        'my.thing.two': 'another',
        'my.thing.three.four': 'deeper'
    }
    with testing.MockConfiguration(conf, namespace=ATestingSchema.namespace):
        yield


class TestSchemaAcceptance:

    def test_schema(self, testing_schema_namespace):
        config_schema = ATestingSchema()
        assert_equal(config_schema.some_value, 'deeper')
        assert_equal(config_schema.one, 1)
        assert_equal(config_schema.two, 'another')
