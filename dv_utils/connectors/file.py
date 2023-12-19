from dv_utils.connectors.connector import Configuration
from urllib.parse import urlparse
import requests
import logging
import os
import copy

logger = logging.getLogger(__name__)


class FileConfiguration(Configuration):
    schema_file = "file.json"
    url = None
    file_name = None
    download_directory = None


class FileConnector():
    config: FileConfiguration

    def __init__(self, config: FileConfiguration) -> None:
        self.config = copy.copy(config)

        if not self.config.file_name:
            self.config.file_name = urlparse(self.config.url).netloc

    def get(self):
        response = requests.get(self.config.url)
        with open(os.path.join(self.config.download_directory, self.config.file_name), 'w') as file:
            file.write(response.text)
