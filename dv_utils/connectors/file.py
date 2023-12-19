from connectors.connector import Configuration
from urllib.parse import urlparse
import requests
import logging
import os
import copy

logger = logging.getLogger(__name__)


class FileConfiguration(Configuration):
    schema_file = "file.json"
    url = None
    fileName = None
    downloadDir = None


class FileConnector():
    config: FileConfiguration

    def __init__(self, config: FileConfiguration) -> None:
        self.config = copy.copy(config)

        if not self.config.fileName:
            self.config.fileName = urlparse(self.config.url).netloc

    def get(self):
        response = requests.get(self.config.url)
        with open(os.path.join(self.config.download_dir, self.config.fileName), 'w') as file:
            file.write(response.text)
