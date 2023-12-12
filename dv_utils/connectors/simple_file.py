from .connector import Connector
from urllib.parse import urlparse
import requests
import logging

logger = logging.getLogger(__name__)

class SimpleFileConfiguration():
    url = None
    fileName = None

class SimpleFileConnector(Connector):
    config: SimpleFileConfiguration = None
    def __init__(self, config: SimpleFileConfiguration) -> None:
        super().__init__()
        if not config.url:
            logger.error('No url passed to configuration')

        if not config.fileName:
            config.fileName = urlparse(config.url).netloc

        self.config = config

    def get(self):
        response = requests.get(self.config.url)
        with open('/resources/data/' + self.config.fileName, 'w') as file:
            file.write(response.text)