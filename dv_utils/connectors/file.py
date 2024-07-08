from dv_utils.connectors.connector import Configuration
from urllib.parse import urlparse
import requests
import os
import copy
import cloudscraper
from dv_utils import audit_log, LogLevel

class FileConfiguration(Configuration):
    schema_file = "file.json"
    url = None
    file_name = None
    download_directory = None
    use_scraper = None


class FileConnector():
    config: FileConfiguration

    def __init__(self, config: FileConfiguration) -> None:
        self.config = copy.copy(config)

        if not self.config.file_name:
            self.config.file_name = urlparse(self.config.url).netloc

    def get(self):
        urls = self.config.url.split(',')
        file_names = self.config.file_name.split(',')

        if len(urls) != len(file_names):
            audit_log(f'Length of urls and file list should be the same. Got {len(urls)} and {len(file_names)}', level=LogLevel.ERROR)
            return
        
        for i in range(len(urls)):
            self.__get_file(urls[i].strip(), file_names[i].strip())
    
    def __get_file(self, url, file_name):
        if(self.config.use_scraper):
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
        else:
            response = requests.get(url)
        
        is_valid = self.__handle_response(response)
        if(is_valid):
            with open(os.path.join(self.config.download_directory, file_name), 'w') as file:
                file.write(response.text)
        else:
            audit_log(f'Could not download file {file_name} from {url}. Got {response.status_code}', level=LogLevel.ERROR)
        audit_log(f'Downloaded {file_name}')
    
    def __handle_response(self, response) -> bool :
        if(response.status_code > 399):
            audit_log(f"Response returned status code [{response.status_code}]", level=LogLevel.WARN)
            return False
        
        return True
