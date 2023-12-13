from .connector import Connector, Config
from urllib.parse import urlparse
import requests
import logging

logger = logging.getLogger(__name__)


class SimpleFileConfiguration(Config):
    def __init__(self) -> None:
        super().__init__()

    url = None
    fileName = None


class SimpleFileConnector(Connector):
    config: SimpleFileConfiguration = None

    def __init__(self, config: SimpleFileConfiguration) -> None:
        super().__init__(config)

        if not self.config.url:
            logger.error('No url passed to configuration')

        if not self.config.fileName:
            self.config.fileName = urlparse(self.config.url).netloc

    def get(self):
        response = requests.get(self.config.url)
        with open(self.config.download_dir + self.config.fileName, 'w') as file:
            file.write(response.text)
