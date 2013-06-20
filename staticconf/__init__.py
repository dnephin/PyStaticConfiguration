from staticconf import config
from staticconf.loader import *
from staticconf.getters import *
from staticconf.readers import *


version         = "0.5.4.1"

view_help       = config.view_help
reload          = config.reload
validate        = config.validate
ConfigurationWatcher = config.ConfigurationWatcher
ConfigFacade    = config.ConfigFacade
