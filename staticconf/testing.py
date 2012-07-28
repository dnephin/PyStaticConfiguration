import mock
from staticconf import config, loader

class MockConfiguration(object):
    """Convenience object for mocking configuration in tests."""

    def __init__(self, *args, **kwargs):
        self.config_data = dict(*args, **kwargs)

    def setup(self):
        config.reload()
        config_path         = 'staticconf.config.configuration_values'
        self.config_patcher = mock.patch.dict(config_path)
        self.mock_config    = self.config_patcher.start()
        loader.DictConfiguration(self.config_data)
        return self.mock_config

    def teardown(self):
        self.config_patcher.stop()
        config.reload()

    def __enter__(self):
        return self.setup()

    def __exit__(self, *args):
        self.teardown()
