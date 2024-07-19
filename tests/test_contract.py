"""
Unit test for the contract module.
"""

import unittest

from dv_utils import ContractQualityCheck, default_settings, process_event_dummy

default_settings.load_settings(".env")

collaboration_space_id="ekmdkbfa"
data_descriptor_id_s3="6668af7559b8b33c82a71c87"
data_descriptor_id_gcs="6668af1259b8b33c82a71bba"
data_descriptor_id_azure="6668af5c59b8b33c82a71c72"
data_connector_config_dir = "tests/fixtures"


class Test(unittest.TestCase):
    """
    Collection of test related to the contract
    """

    def setUp(self):
        self.ContractQualityCheck = ContractQualityCheck()


    def test_contract_quality_check(self):
        # """
        # Try to check a contract of a custom dataset on s3
        # """
        # self.ContractQualityCheck.check_contract_for_data_descriptor(collaboration_space_id,data_descriptor_id_s3,data_connector_config_dir)

        # """
        # Try to check a contract of a custom dataset on gcs
        # """
        # self.ContractQualityCheck.check_contract_for_data_descriptor(collaboration_space_id,data_descriptor_id_gcs,data_connector_config_dir)

        # """
        # Try to check a contract of a custom dataset on azure
        # """
        # self.ContractQualityCheck.check_contract_for_data_descriptor(collaboration_space_id,data_descriptor_id_azure,data_connector_config_dir)

        """
        Try to check contract for a collaboration space
        """
        self.ContractQualityCheck.check_contracts_for_collaboration_space(collaboration_space_id,data_connector_config_dir)

        # """
        # Try to check a contract of a non-existing collaboration space
        # """
        # self.ContractQualityCheck.check_contracts_for_collaboration_space( None, data_connector_config_dir)

        # """
        # Try to check a contract of a non-existing descriptor 
        # """
        # self.ContractQualityCheck.check_contract_for_data_descriptor(collaboration_space_id,None,data_connector_config_dir)

