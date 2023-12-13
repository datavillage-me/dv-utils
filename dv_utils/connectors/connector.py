import copy


class Config(object):
    download_dir = None


class Connector(object):

    config: Config = None

    def __init__(self, config: Config):
        self.config = copy.copy(config)

        if not self.config.download_dir:
            self.config.download_dir = '/resources/data'

    def get(self):
        pass
