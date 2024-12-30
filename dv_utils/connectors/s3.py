import logging
import copy
import duckdb

from dv_utils.connectors.connector import Configuration
from ..secret_manager import SecretManager
from ..log_utils import audit_log, LogLevel

logger = logging.getLogger(__name__)

#TODO add workload identity federation pattern
class S3Configuration(Configuration):
    schema_file = "s3.json"
    connect_type ="S3"
    
    description = None
    location = None
    file_format = None
    encryption_key = None

    region = None
    key_id = None
    secret = None

#TODO add writer (for data user output connector)
class S3Connector():
    NAMING_CONVENTION_MODEL="{{model}}"

    config: S3Configuration

    def __init__(self, config: S3Configuration) -> None:
        self.config = copy.copy(config)
        self.duckdb_connection=None
        self.SecretManager=SecretManager()

    def add_duck_db_connection(self,duckdb):
        encryption_key=self.config.encryption_key
        ref_encryption_key = self.config.connector_id

        region=self.config.region
        key_id=self.config.key_id
        secret=self.config.secret
        self.duckdb_connection=duckdb

        if encryption_key!=None:
            duckdb.sql(f"PRAGMA add_parquet_key('{ref_encryption_key}', '{encryption_key}')")
        duckdb.sql(f"CREATE OR REPLACE SECRET (TYPE S3,KEY_ID '{key_id}',SECRET '{secret}',REGION '{region}');")

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
    
    #TODO code duplicate with other connectors.
    def export_duckdb(self,model_key):
        #replace {model} by the model key if any reference to {model}  in the data source location
        data_source_location_for_model=self.config.location.replace(self.NAMING_CONVENTION_MODEL.format(),model_key)
        logger.debug(f"Used data source location: {data_source_location_for_model}")
        target=""
        if self.config.file_format=="parquet":
            if self.config.encryption_key!="":
                encryption_config_str="encryption_config {footer_key: '"+self.config.connector_id+"'}"
            target=f"'{data_source_location_for_model}' ({encryption_config_str})"
        elif self.config.file_format=="json":
            target=f"'{data_source_location_for_model}'"
        elif self.config.file_format=="csv":
            target=f"'{data_source_location_for_model}' (HEADER, DELIMITER ',')"
        else:
            logger.error("Format not supported by duckdb")
        export_sql=f"COPY {model_key} TO {target}"
        self.duckdb_connection.sql(export_sql)
    
    #TODO code duplicate with other connectors.
    #TODO only work with signed json export - needs to be extended to other supported format parquet and csv
    def export_signed_output_duckdb(self,model_key:str,collaboration_space_id:str):
        #get data from model_key in memory db as json
        query=f"SELECT * FROM {model_key}"
        df=self.duckdb_connection.sql(query).df()
        json_payload=df.to_json(orient = 'records')
        #create signed json
        signed_json=self.SecretManager.sign_json(collaboration_space_id,json_payload)
        
        #insert into duckdb for export
        table_name="signed_json_"+model_key
        query=f"CREATE OR REPLACE TABLE {table_name} (payload VARCHAR,protected VARCHAR,signature VARCHAR)"
        self.duckdb_connection.sql(query)
        query=f"INSERT INTO {table_name} VALUES ('{signed_json['payload']}','{signed_json['protected']}','{signed_json['signature']}')"
        self.duckdb_connection.sql(query)
        self.export_duckdb(table_name)