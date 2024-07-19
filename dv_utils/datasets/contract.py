"""
This module define the data contracts for the dv-utils package.
"""
import logging
import yaml

from ..settings import Settings
from ..settings import settings as default_settings

from ..connectors.connector import populate_configuration
from ..connectors import s3,gcs,azure

from datacontract.data_contract import DataContract
from datacontract.data_contract import Server

logger = logging.getLogger(__name__)


class Contract:

    def __init__(self, settings: Settings = None):
        self.settings: Settings = settings or default_settings
        self.data_contract=None
        self.collaboration_space_id=None
        self.data_descriptor_id=None
        self.connector=None
        self.data_connector_config_path=None

    def create_contract(self, data_descriptor: str,collaboration_space_id: str, data_descriptor_id: str,data_connector_config_path:str):
        #TODO
        #add version in custom data contract as an attribute in the console
        #code part with pre-defined dataset
        #look into filter datasets "echantillonage" to not load all the data https://docs.soda.io/soda-cl/filters.html#in-check-vs-dataset-filters
        self.collaboration_space_id=collaboration_space_id
        self.data_descriptor_id=data_descriptor_id
        self.data_connector_config_path=data_connector_config_path
        if data_descriptor != None :
            self.__init_data_connector(data_descriptor)
            data_contract_yaml=self.__data_descriptor_to_data_contract(data_descriptor)
            try:
                logger.info(f"Create data contract object")
                data_contract = DataContract(data_contract_str=data_contract_yaml)
                self.data_contract=data_contract
            except Exception as inst:
                logger.error(Exception)
                raise
        else:  
            logger.error(f"No data contract available")
            raise RuntimeError("Unable to create data contract")

    def __init_data_connector(self,data_descriptor: str):
        try:
            data_source_type=data_descriptor["settings"]["type"] 
            logger.info(f"Initialise data connector for data source: type={data_source_type}")
            #initialise datavillage connector to get access to data source access keys
            #TODO add other type
            if data_source_type=="s3":
                config = s3.S3Configuration()
                if self.data_connector_config_path!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_path)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = s3.S3Connector(config)
            if data_source_type=="gcs":
                config = gcs.GCSConfiguration()
                if self.data_connector_config_path!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_path)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = gcs.GCSConnector(config)
            if data_source_type=="azure":
                config = azure.AZConfiguration()
                if self.data_connector_config_path!="":
                    populate_configuration(self.data_descriptor_id,config,self.data_connector_config_path)
                else:
                    populate_configuration(self.data_descriptor_id,config)
                self.connector = azure.AZConnector(config)
        except Exception as inst:
            logger.error(Exception)
            raise RuntimeError(f"Unable to initialise connector: {inst}")

    def __data_descriptor_to_data_contract(self,data_descriptor: str):
        try: 
            if data_descriptor["kind"]=="Dataset":
                #TODO
                s=0
            else:
                data_contract_yaml=f'''
dataContractSpecification: 0.9.3
id: urn:datacontract:{data_descriptor["id"]}
info:
  title: {data_descriptor["name"]}
  version: custom
  description: {data_descriptor["description"]}
'''
            if data_descriptor["schema"]!="":
                data_contract_yaml+=f'''
models:
  {data_descriptor["schema"]}
'''
            if data_descriptor["syntheticData"]!="":
                data_contract_yaml+=f'''
examples:
  {data_descriptor["syntheticData"]}
'''
            return data_contract_yaml
        except Exception as inst:
            logger.error(Exception)
            raise RuntimeError(f"Unable to transform data descriptor into data contract: {inst}")
        