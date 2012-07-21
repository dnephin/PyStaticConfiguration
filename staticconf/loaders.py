

class ConfigurationLoader(object):
    
    def validate_keys(self):
        pass

class YamlConfiguration(ConfigurationLoader):

    def __init__(self, file=None, error_on_unknown=False):
        import yaml
        self.data = yaml.load(file)
        if error_on_unknown:
            self.validate_keys()

