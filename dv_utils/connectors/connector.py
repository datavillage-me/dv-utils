import copy
import json
from typing import TypeVar


class Config():
    download_dir = None


class Connector():

    config = None

    def __init__(self, config):
        self.config = copy.copy(config)

        if not self.config.download_dir:
            self.config.download_dir = '/resources/data'

    def get(self):
        pass


T = TypeVar('T')


def populate_configuration(connector_id, config: T, config_dir='/resources/data') -> T:
    filename = f'{config_dir}/configuration_{connector_id}.json'
    with open(filename, 'r') as file:
        data = json.load(file)
        keys = data['connectorKeys']

        parameters = [str.upper(a)
                      for a in dir(config) if not a.startswith('__')]

        for p in parameters:
            if (p in keys):
                setattr(config, str.lower(p), keys[p])

        return config
