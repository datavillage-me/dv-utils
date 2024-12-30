"""
Unit test for the contract module.
"""

import unittest
import json
import io  

from dv_utils import SecretManager, default_settings

default_settings.load_settings(".env")

collaboration_space_id="ekmdkbfa"

class Test(unittest.TestCase):
    """
    Collection of test related to the secret manager
    """

    def setUp(self):
        self.SecretManager = SecretManager()
    
    def test_sign_file(self):
        with open("tests/outputs/quality_checks.json", "rb") as file:
            files = {'file': file}
            signed_file=self.SecretManager.sign(files)
            print(signed_file)

    def test_sign_string(self):  
        # The content of your string
        content = "This is the content of the string."
        signed_string=self.SecretManager.sign_string(content)
        print(signed_string)
    
    def test_sign_json(self):  
        # The content of your string
        content = {"test":"test"}
        signed_json=self.SecretManager.sign_json(collaboration_space_id,content)
        print(signed_json)
