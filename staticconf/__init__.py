from staticconf import config
from staticconf.loader import *
from staticconf.getters import *
from staticconf.readers import *


version         = "0.6.0"

view_help       = config.view_help
reload          = config.reload
validate        = config.validate
ConfigurationWatcher = config.ConfigurationWatcher
ConfigFacade    = config.ConfigFacade
