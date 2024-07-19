"""
Unit test for the contract module.
"""

import unittest
import json

from dv_utils import ContractManager, default_settings

default_settings.load_settings(".env")

collaboration_space_id="ekmdkbfa"
data_descriptor_id_s3="6668af7559b8b33c82a71c87"
data_descriptor_id_gcs="6668af1259b8b33c82a71bba"
data_descriptor_id_azure="6668af5c59b8b33c82a71c72"
data_descriptor_id_file="6668af7559b8b33c82a71c89"


class Test(unittest.TestCase):
    """
    Collection of test related to the contract
    """

    def setUp(self):
        self.ContractManager = ContractManager()


    def test_contract_quality_check(self):
        """
        Try to check a contract of a custom dataset on github with file connector. Use this test to check a quality check that does not pass
        """
        filename = f'tests/fixtures/descriptor_file_{data_descriptor_id_file}.json'
        with open(filename, 'r') as file:
            data = json.load(file)
            self.ContractManager.check_contract_for_data_descriptor(data_descriptor_id_file,data)


        """
        Try to check a contract of a custom dataset on s3
        """
        filename = f'tests/fixtures/descriptor_s3_{data_descriptor_id_s3}.json'
        with open(filename, 'r') as file:
            data = json.load(file)
            self.ContractManager.check_contract_for_data_descriptor(data_descriptor_id_s3,data)


        """
        Try to check a contract of a custom dataset on gcs
        """
        filename = f'tests/fixtures/descriptor_gcs_{data_descriptor_id_gcs}.json'
        with open(filename, 'r') as file:
            data = json.load(file)
            self.ContractManager.check_contract_for_data_descriptor(data_descriptor_id_gcs,data)

        """
        Try to check a contract of a custom dataset on azure
        """
        filename = f'tests/fixtures/descriptor_az_{data_descriptor_id_azure}.json'
        with open(filename, 'r') as file:
            data = json.load(file)
            self.ContractManager.check_contract_for_data_descriptor(data_descriptor_id_azure,data)

        """
        Try to check contract for a collaboration space
        """
        self.ContractManager.check_contracts_for_collaboration_space(collaboration_space_id)

        """
        Try to check a contract of a non-existing collaboration space
        """
        self.ContractManager.check_contracts_for_collaboration_space( None)

        """
        Try to check a contract of a non-existing descriptor 
        """
        self.ContractManager.check_contract_for_data_descriptor(None,None)
