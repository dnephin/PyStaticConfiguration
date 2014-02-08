from staticconf import config
from staticconf.loader import *   # flake8: noqa
from staticconf.getters import *  # flake8: noqa
from staticconf.readers import *  # flake8: noqa


version         = "0.6.0"

view_help       = config.view_help
reload          = config.reload
validate        = config.validate
ConfigurationWatcher = config.ConfigurationWatcher
ConfigFacade    = config.ConfigFacade
