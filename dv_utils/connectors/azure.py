import logging
import copy
import duckdb

from dv_utils.connectors.connector import Configuration
from ..log_utils import audit_log, LogLevel

logger = logging.getLogger(__name__)

class AZConfiguration(Configuration):
    schema_file = "azure.json"
    connect_type ="azure"
    
    description = None
    location = None
    file_format = None
    encryption_key = None
    ref_encryption_key = None

    connection_key = None
    share_access_token = None

class AZConnector():
    NAMING_CONVENTION_MODEL="{{model}}"

    config: AZConfiguration

    def __init__(self, config: AZConfiguration) -> None:
        self.config = copy.copy(config)

    def add_duck_db_connection(self,duckdb,ref_encryption_key: str):
        description = self.config.description
        location = self.config.location
        file_format = self.config.file_format
        encryption_key=self.config.encryption_key
        ref_encryption_key = self.config.ref_encryption_key

        connection_key=self.config.connection_key
        share_access_token=self.config.share_access_token

        if encryption_key!=None:
            duckdb.sql(f"PRAGMA add_parquet_key('{ref_encryption_key}', '{encryption_key}')")
        #TODO solve issue with connection key and certificate with duckdb
        duckdb.sql(f"CREATE OR REPLACE SECRET (TYPE AZURE,CONNECTION_STRING '{connection_key}');")

        return duckdb
    
    #TODO code duplicate with other connectors.
    def get_duckdb_source(self,model_key: str,options:str):
        #replace {model} by the model key if any reference to {model}  in the data source location
        data_source_location_for_model=self.config.location.replace(self.NAMING_CONVENTION_MODEL.format(),model_key)
        logger.info(f"Used data source location for model {model_key}: {data_source_location_for_model}")
        if options!="":
                options=","+options
        if self.config.file_format=="parquet":
            if self.config.ref_encryption_key!="":
                encryption_config_str=", encryption_config = {footer_key: '"+self.config.ref_encryption_key+"'}"
            return f"read_parquet('{data_source_location_for_model}'{options}{encryption_config_str})"
        elif self.file_format=="json":
            return f"read_json('{data_source_location_for_model}'{options})"
        elif self.file_format=="csv":
            return f"read_csv('{data_source_location_for_model}'{options})"
        else:
            logger.error("Format not supported by duckdb")



        
