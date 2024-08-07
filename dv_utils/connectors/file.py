from dv_utils.connectors.connector import Configuration
from urllib.parse import urlparse
import logging
import requests
import os
import copy
import cloudscraper
from ..log_utils import audit_log, LogLevel

logger = logging.getLogger(__name__)

class FileConfiguration(Configuration):
    schema_file = "file.json"
    connect_type ="File"

    url = None
    location = None
    file_name = None
    download_directory = None
    use_scraper = None
    file_format = None
    encryption_key = None


class FileConnector():
    NAMING_CONVENTION_MODEL="{{model}}"

    config: FileConfiguration

    def __init__(self, config: FileConfiguration) -> None:
        self.config = copy.copy(config)
        #manage backward compatibility with url property. Standard common property used in dv-utils for all connector is "location"
        self.config.location=self.config.url

        if not self.config.file_name:
            self.config.file_name = urlparse(self.config.url).netloc

    def get(self):
        #get the file with http request
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
    
    def add_duck_db_connection(self,duckdb):
        encryption_key=self.config.encryption_key
        ref_encryption_key = self.config.connector_id

        if encryption_key!=None:
            duckdb.sql(f"PRAGMA add_parquet_key('{ref_encryption_key}', '{encryption_key}')")
        return duckdb
    
    #TODO code duplicate with other connectors.
    def get_duckdb_source(self,model_key: str="",options:str=""):
        #replace {model} by the model key if any reference to {model}  in the data source location
        data_source_location_for_model=self.config.location
        if model_key!= "":
            data_source_location_for_model=self.config.location.replace(self.NAMING_CONVENTION_MODEL.format(),model_key)
        logger.debug(f"Used data source location: {data_source_location_for_model}")
        if options!="":
                options=","+options
        if self.config.file_format=="parquet":
            if self.config.encryption_key!="":
                encryption_config_str=", encryption_config = {footer_key: '"+self.config.connector_id+"'}"
            return f"read_parquet('{data_source_location_for_model}'{options}{encryption_config_str})"
        elif self.config.file_format=="json":
            return f"read_json('{data_source_location_for_model}'{options})"
        elif self.config.file_format=="csv":
            return f"read_csv('{data_source_location_for_model}'{options})"
        else:
            logger.error("Format not supported by duckdb")
