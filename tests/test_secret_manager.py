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
    
    def test_decrypt_file(self):
        with open("tests/outputs/encrypted_file.txt", "rb") as file:
            files = {'message': file}
            decrypted_file=self.SecretManager.decrypt(files)
            print(decrypted_file)

    def test_decrypt_encoded_string(self):  
        # The content of your string
        content = "ewogICJwYXNzcGhyYXNlIjogIkpPQ0Zsbjh5V2dNS1Y2d0tQNUo5UDhVSEZwVDlkV1ZEbStqLzhKcm1rQkd3c1N3bkMxc1hDY0w1WnpZV2JaRW1hYTNTWklEZW0vWDhYbzZ3Q2t3cUtOaXF4VE9EalcwWTE4MThpTE11V0RFMDc2b2VseHowRVYyQmlscExoZjFkSWN6RDhCWEJ6U2IrS3VSZlZMSVo1NG5QSEpiTVBnNnJTSnRqSUNzN1ZjVllhQkFhSElicE1XbDlNaGV2Rm0veHc0V1U4UkNYMGZxYWZzVWFiUFJLRVUxWmlKc0U5a0hqMndDLzZtblZha21sY1pQQ0VUbnMwN1hQNURleHJxa3dEemZkZ25PTEU2eExmd1NwRzQ3YUFCVzJCOTVGZVdHNU8zQ0lKVXlCR2J5SE1sSFVJTGZXa2l0UFRJa1cxejhLaFIyaFFBa1dxanowaXlEZGlJQVhWUT09IiwKICAiY29udGVudCI6ICJVMkZzZEdWa1gxOEE4WWZjMEFZK0dLRDhBOXdGUlZRbndXalRzcldib2dEaktPdStlOXJHa1Y3eWY1SWxWWit6Igp9"
        decrypted_string=self.SecretManager.decrypt_encoded_string(content)
        print(decrypted_string)
