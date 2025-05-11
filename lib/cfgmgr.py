import os
import json
import logger

class config_manager:
    _default_config = {
        'debug': False,
        'name': 'server',
        'host': 'localhost',
        'port': 7901
    }
    _required_info = {
        'debug': bool,
        'name': str,
        'host': str,
        'port': int
    }
    def _fill_config(self, config: dict):
        if(not isinstance(config, dict)): return config

        # iterates, checks variable type if variable exists, else updates dictionary
        for y in self._required_info.items():
            if(y[0] in config):
                val = config.get(y[0])
                if(not isinstance(val, y[1])): raise ValueError(f'Value for variable {y[0]} must be of type {y[1].__name__}, not {type(val).__name__}')
            else: 
                config.update({y[0]: self._default_config.get(y[0])})
        return config

    def __init__(self, file_path: str = None, config: dict = None):
        self.file_path = file_path

        # load config either from file or dictionary
        if(file_path is not None):
            if(not isinstance(file_path, str)): raise ValueError(f'File path must be a string, not {type(file_path).__name__}')
            if(not os.path.exists(file_path)): raise FileNotFoundError(f'File not found at {file_path}')
            with open(file_path, 'r') as f: config = json.loads(f.read())
            self.config = self._fill_config(config)
        elif(config is not None):
            if(not isinstance(config, dict)): raise ValueError(f'Config must be a dictionary, not {type(config).__name__}')
            self.config = self._fill_config(config)
        else:
            logger.warn('no config passed, falling back to default')
            self.config = self._default_config

        logger.debug('loaded config')

    def get(self, key):
        if(not isinstance(key, str)): raise ValueError(f'key must be of type str, not {type(key).__name__}')

        if(self._required_info.get(key) is not None):
            return self._required_info.get(key)(self.config.get(key))
        else: self.config.get(key)

    def set(self, key: str, value):
        if(not isinstance(key, str)): raise ValueError(f'key must be of type str, not {type(key).__name__}')
        if(not isinstance(value, self._required_info.get(key))): raise ValueError(f'value for key {key} must be of type {self._required_info.get(key)}, not {type(value).__name__}')
        self.config.update({key: value})