"""
This module defines the data contracts for the dv-utils package.
"""
import yaml
import json

import duckdb
from soda.scan import Scan
from datacontract.data_contract import DataContract

from ..settings import Settings
from ..settings import settings as default_settings

from ..connectors.connector import populate_configuration
from ..connectors import s3,gcs,azure,file

from ..log_utils import log, LogLevel

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
                log(f"Create data contract object", LogLevel.DEBUG)
                self.data_contract = DataContract(data_contract_str=json.dumps(data_contract_yaml))
            except Exception as inst:
                log(f"Unable to create data contract: {inst}", LogLevel.ERROR)
                raise
        else:  
            log(f"Unable to create data contract - No data descriptor available", LogLevel.ERROR)
            raise Exception(f"Unable to create data contract - No data descriptor available")
    
    def check_contract(self):   
        try:
            if self.connector!=None and self.connector.config.location!=None and self.connector.config.file_format!=None:
                #use duck db to fetch data for quality check
                log(f"Connect with duckdb", LogLevel.DEBUG)
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
                        log(f"{self.connector.format} not supported for data contract check. Only parquet, json or csv are supported", LogLevel.ERROR) 
                        raise Exception("Unable to check data contract")
                #Start quality check with soda
                log(f"Running engine soda-core", LogLevel.DEBUG)
                sodacl_contract=self.data_contract.export("sodacl")
                sodacl_contract_yaml=yaml.safe_load(sodacl_contract)
                scan_results={}
                for soda_check in sodacl_contract_yaml:
                    soda_check_yaml=sodacl_contract_yaml.get(soda_check, [])
                    log("Starting soda scan for model - "+soda_check, LogLevel.DEBUG)
                    scan = Scan()
                    scan.add_duckdb_connection(duckdb_connection=con, data_source_name=self.connector.config.connector_id)
                    scan.set_data_source_name(self.connector.config.connector_id)
                    #add sodaCL checks per model - small trick is to add the soda_check string with carriage return to make the yaml str comply with soda check format
                    scan.add_sodacl_yaml_str(soda_check+":\n"+yaml.dump(soda_check_yaml))
                    scan.execute()
                    #This is a bug in soda. I need to "flush" the logs to avoid keeping logs error items in log history
                    scan._logs=None
                    log("Finished soda scan", LogLevel.DEBUG)
                    #get results
                    scan_result = scan.get_scan_results()
                    if(scan_result['hasErrors'] or scan_result['hasFailures']):
                        string_to_log=f'Quality check done data descriptor {self.data_descriptor_id}. Scan result NOK'
                        log(string_to_log,LogLevel.WARN)
                    else:
                        string_to_log=f'Quality check done data descriptor {self.data_descriptor_id}. Scan result OK'
                        log(string_to_log, LogLevel.DEBUG)
                    scan_results[soda_check]=scan_result
                #return results in json to the caller for further user (show to end user, ...)
                return scan_results
            else:
                log(f"No connector defined in the data contract or missing argument (location or format)", LogLevel.ERROR) 
                raise Exception("Unable to check data contract")
        except Exception as inst:
            log(f"Unable to check data contract {inst}", LogLevel.ERROR)
            raise

    def export_contract_to_sql_create_table(self,model_key:str): 
        log(f"Get all fields from data contract model - "+model_key, LogLevel.DEBUG)
        spec_yaml = yaml.safe_load(self.data_contract.get_data_contract_specification().to_yaml())
        fields=spec_yaml["models"][model_key]["fields"]
        log(f"Create SQL query for model - "+model_key, LogLevel.DEBUG)
        if len(fields)<=0:
            log(f"Unable to initialise export contract to sql create table: No fields in the data contract", LogLevel.ERROR)
            raise 
        query="CREATE OR REPLACE TABLE "+model_key+ "("
        for field_name in fields:
            field_type=spec_yaml["models"][model_key]["fields"][field_name]["type"]
            query=query+str(field_name)+" "+field_type.upper()+","
        query=query[:-1]+")"
        log(query, LogLevel.DEBUG)
        return query

    def __init_data_connector(self,data_source_type: str):
        try:
            log(f"Initialise data connector for data source: type={data_source_type}", LogLevel.DEBUG)
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
                log(f"Unable to initialise connector, data source type {data_source_type} unknown.", LogLevel.ERROR)
                raise
        except Exception as inst:
            log(f"Unable to initialise connector: {inst}", LogLevel.ERROR)
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
            log(f"Unable to transform data descriptor into data contract: {inst}", LogLevel.ERROR)
            raise
        