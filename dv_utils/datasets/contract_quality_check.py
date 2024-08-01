"""
This module checks quality of a dataset in a data source for checks defined by the data contract.
"""
import logging
import yaml

import duckdb

from ..settings import Settings
from ..settings import settings as default_settings

from ..log_utils import audit_log, LogLevel

from ..client import Client

from ..connectors.connector import populate_configuration
from ..connectors import s3

from .contract import Contract

from soda.scan import Scan

logger = logging.getLogger(__name__)


class ContractQualityCheck:
    NAMING_CONVENTION_MODEL="{{model}}"

    def __init__(self):
        self.client= Client()
        self.contract=Contract()
        self.data_connector_config_location=default_settings.data_connector_config_location
    
    def check_contract_for_data_descriptor(self, data_descriptor_id: str, data_descriptor: str):
         if data_descriptor != None:
            self.contract.create_contract(data_descriptor,None,data_descriptor_id)
            return self.__check_contract(self.contract)
         else:
            logger.error(f"No data descriptor available: data_descriptor_id:{data_descriptor_id}")
            raise RuntimeError("Unable to check data contract")
    
    def check_contracts_for_collaboration_space(self, collaboration_space_id: str):
        scan_results={}
        logger.info(f"Get list of data providers for:{collaboration_space_id}")
        list_participants=self.client.get_list_of_participants(collaboration_space_id,self.client.DATA_PROVIDER_COLLABORATOR_ROLE_VALUE)
        if list_participants != None and len(list_participants)>0:
            for participant in list_participants:
                client_id=participant["clientId"]
                data_descriptors=participant.get("dataDescriptors")
                if len(data_descriptors) > 0:
                    for data_descriptor in data_descriptors:
                        self.contract.create_contract(data_descriptor,collaboration_space_id,data_descriptor["id"])
                        scan_results[data_descriptor["id"]]=self.__check_contract(self.contract)
                else:
                    logger.error(f"No data descriptor available for collaboration_space_id:{collaboration_space_id}")
                    raise RuntimeError("Unable to check data contract")
        else:
            logger.error(f"No participant as data provider available for collaboration_space_id:{collaboration_space_id}")
            raise RuntimeError("Unable to check data contract")
        return scan_results


    def __check_contract(self,contract: Contract):   
        try:
            if contract.connector!=None and contract.connector.config.location!=None and contract.connector.config.file_format!=None:
                #use duck db to fetch data for quality check
                logger.info(f"Connect with duckdb")
                con = duckdb.connect(database=":memory:")
                con = contract.connector.add_duck_db_connection(con)
                #loop on all models
                data_contract_spec=contract.data_contract.get_data_contract_specification()
                for model_key, model_value in data_contract_spec.models.items():
                    if contract.connector.config.file_format=="parquet" or contract.connector.config.file_format=="json" or contract.connector.config.file_format=="csv":
                        if contract.connector.config.file_format=="parquet":
                            options="hive_partitioning=1"
                        else:
                            options=""
                        con.sql(f"""
                        CREATE VIEW "{model_key}" AS SELECT * FROM {contract.connector.get_duckdb_source(model_key,options)};
                        """)
                    else:
                        logger.error(f"{contract.connector.format} not supported for data contract check. Only parquet, json or csv are supported") 
                        raise RuntimeError("Unable to check data contract")
                    #Start quality check with soda
                    logger.info(f"Running engine soda-core")
                    logger.info(f"Export data contract to soda checks")
                    sodacl_contract=contract.data_contract.export("sodacl")
                    scan = Scan()
                    scan.add_duckdb_connection(duckdb_connection=con, data_source_name=contract.connector.config.connect_type)
                    scan.set_data_source_name(contract.connector.config.connect_type)
                    scan.add_sodacl_yaml_str(sodacl_contract)
                    logging.info("Starting soda scan")
                    scan.execute()
                    logging.info("Finished soda scan")
                    #get results and log into audit logs 
                    scan_results = scan.get_scan_results()
                    if(scan_results['hasErrors'] or scan_results['hasFailures']):
                        string_to_log=f'Quality check done for Collaboration Space {contract.collaboration_space_id}, Data descriptor {contract.data_descriptor_id}. Scan result NOK'
                        logging.error(string_to_log)
                        #TODO reactivate audit log
                        #audit_log(string_to_log, level=LogLevel.ERROR)
                    else:
                        string_to_log=f'Quality check done for Collaboration Space {contract.collaboration_space_id}, Data descriptor {contract.data_descriptor_id}. Scan result OK'
                        logging.info(string_to_log)
                        #TODO reactivate audit log
                        #audit_log(string_to_log, level=LogLevel.INFO)
                    #return results to the caller for further user (show to end user, ...)
                    return scan_results
                else:
                    logger.error(f"No connector defined in the data contract or missing argument (location or format)") 
                    raise RuntimeError("Unable to check data contract")
        except Exception as inst:
            logger.error(inst)
            raise inst