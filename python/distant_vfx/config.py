import logging
from yaml import safe_load, YAMLError

LOG = logging.getLogger(__name__)


class Config:

    def __init__(self):
        self.config_path = None
        self.data = None

    def load_config_data(self, config_path):
        config_did_load = self.load_config(config_path)
        if config_did_load:
            return self.data
        return None

    def load_config(self, config_path='./config.yml'):
        # Load in sensitive data via a .yml config file.
        with open(config_path, 'r') as file:
            try:
                self.config_path = config_path
                self.data = safe_load(file)
                return True
            except YAMLError as e:
                LOG.error(e)
                return False
