"""
This module defines the data contracts for the dv-utils package.
"""
import logging
import yaml
import json

import duckdb
from soda.scan import Scan
from datacontract.data_contract import DataContract

from ..settings import Settings
from ..settings import settings as default_settings

from ..connectors.connector import populate_configuration
from ..connectors import s3,gcs,azure,file

from ..log_utils import audit_log, LogLevel

logger = logging.getLogger(__name__)


class Contract:

    def __init__(self, settings: Settings = None):
        self.settings: Settings = settings or default_settings
        self.data_contract=None
        self.data_descriptor_id=None
        self.connector=None
        self.data_connector_config_location=default_settings.data_connector_config_location

    def create_contract(self, data_descriptor_id: str, data_source_type: str, data_descriptor:str):
        #TODO
        #add version in custom data contract as an attribute in the console
        #code part with pre-defined dataset
        #look into filter datasets "echantillonage" to not load all the data https://docs.soda.io/soda-cl/filters.html#in-check-vs-dataset-filters
        self.data_descriptor_id=data_descriptor_id
        if data_descriptor != None :
            self.__init_data_connector(data_source_type)
            data_contract_yaml=self.__data_descriptor_to_data_contract(data_descriptor)
            try:
                logger.debug(f"Create data contract object")
                self.data_contract = DataContract(data_contract_str=json.dumps(data_contract_yaml))
            except Exception as inst:
                logger.error(f"Unable to create data contract: {inst}")
                raise
        else:  
            logger.error(f"Unable to create data contract - No data descriptor available")
            raise Exception(f"Unable to create data contract - No data descriptor available")
    
    def check_contract(self):   
        try:
            if self.connector!=None and self.connector.config.location!=None and self.connector.config.file_format!=None:
                #use duck db to fetch data for quality check
                logger.debug(f"Connect with duckdb")
                con = duckdb.connect(database=":memory:")
                con = self.connector.add_duck_db_connection(con)
                #loop on all models
                data_contract_spec=self.data_contract.get_data_contract_specification()
                for model_key, model_value in data_contract_spec.models.items():
                    if self.connector.config.file_format=="parquet" or self.connector.config.file_format=="json" or self.connector.config.file_format=="csv":
                        if self.connector.config.file_format=="parquet":
                            options="hive_partitioning=1"
                        else:
                            options=""
                        con.sql(f"""
                        CREATE OR REPLACE VIEW "{model_key}" AS SELECT * FROM {self.connector.get_duckdb_source(model_key,options)};
                        """)
                    else:
                        logger.error(f"{self.connector.format} not supported for data contract check. Only parquet, json or csv are supported") 
                        raise Exception("Unable to check data contract")
                    #Start quality check with soda
                    logger.debug(f"Running engine soda-core")
                    logger.debug(f"Export data contract to soda checks")
                    sodacl_contract=self.data_contract.export("sodacl")
                    scan = Scan()
                    scan.add_duckdb_connection(duckdb_connection=con, data_source_name=self.connector.config.connector_id)
                    scan.set_data_source_name(self.connector.config.connector_id)
                    scan.add_sodacl_yaml_str(sodacl_contract)
                    logging.debug("Starting soda scan")
                    scan.execute()
                    #This is a bug in soda. I need to "flush" the logs to avoid keeping logs error items in log history
                    scan._logs=None
                    logging.debug("Finished soda scan")
                    #get results
                    scan_results = scan.get_scan_results()
                    if(scan_results['hasErrors'] or scan_results['hasFailures']):
                        string_to_log=f'Quality check done data descriptor {self.data_descriptor_id}. Scan result NOK'
                        audit_log(string_to_log,LogLevel.WARN)
                        logging.error(string_to_log)
                    else:
                        string_to_log=f'Quality check done data descriptor {self.data_descriptor_id}. Scan result OK'
                        audit_log(string_to_log)
                        logging.debug(string_to_log)
                    #return results to the caller for further user (show to end user, ...)
                    return scan_results
                else:
                    logger.error(f"No connector defined in the data contract or missing argument (location or format)") 
                    raise Exception("Unable to check data contract")
        except Exception as inst:
            logger.error(f"Unable to check data contract {inst}")
            raise

    def __init_data_connector(self,data_source_type: str):
        try:
            logger.debug(f"Initialise data connector for data source: type={data_source_type}")
            #initialise datavillage connector to get access to data source access keys
            if data_source_type=="S3":
                config = s3.S3Configuration()
                if self.data_connector_config_location!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_location)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = s3.S3Connector(config)
            elif data_source_type=="Gcs":
                config = gcs.GCSConfiguration()
                if self.data_connector_config_location!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_location)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = gcs.GCSConnector(config)
            elif data_source_type=="Azure":
                config = azure.AZConfiguration()
                if self.data_connector_config_location!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_location)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = azure.AZConnector(config)
            elif data_source_type=="File":
                config = file.FileConfiguration()
                if self.data_connector_config_location!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_location)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = file.FileConnector(config)
            else:
                logger.error(f"Unable to initialise connector, data source type {data_source_type} unknown.")
                raise
        except Exception as inst:
            logger.error(f"Unable to initialise connector: {inst}")
            raise 

    def __data_descriptor_to_data_contract(self,data_descriptor: str):
        try: 
            if data_descriptor["kind"]=="Dataset":
                #TODO implement the creation of the data contract for pre-defined dataset
                pass
            else:
                data_contract_json={}
                data_contract_json["dataContractSpecification"]="1.1.0"
                data_contract_json["id"]=f"urn:datacontract:{data_descriptor['id']}"
                data_contract_json["info"]={"title":data_descriptor["name"],"version": "custom","description": data_descriptor["description"]}
                if isinstance(data_descriptor["schema"], dict):
                    data_contract_json["models"]=data_descriptor["schema"]
                else:
                    data_contract_json["models"]=json.loads(data_descriptor["schema"])
                if "syntheticData" in data_descriptor:
                    if isinstance(data_descriptor["syntheticData"], list):
                        data_contract_json["examples"]=data_descriptor["syntheticData"]
                    else:
                        data_contract_json["examples"]=json.loads(data_descriptor["syntheticData"])
                data_contract_yaml=yaml.dump(data_contract_json,sort_keys=False)
            return yaml.safe_load(data_contract_yaml)
        except Exception as inst:
            logger.error(f"Unable to transform data descriptor into data contract: {inst}")
            raise
        