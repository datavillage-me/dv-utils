"""
This module define the client class to interact with the secret manager.
The secret manager end points are only accssible by the algorithm running in the confidential environement and are not exposed to the internet.
"""

import logging
import json
import io
import requests
import base64

from typing import Literal

from .settings import Settings
from .settings import settings as default_settings
from .client import Client

logger = logging.getLogger(__name__)


class SecretManager:
    def __init__(self, settings: Settings = None):
        self.settings: Settings = settings or default_settings
        self.base_url=default_settings.secret_manager_url
        self.client= Client()

    def sign(self, files):
        """
        sign the opened binary files with the private key linked to the confidential environment
        the files needs to be structured like the following files = {'file': file} as in python request object
        """
        try:
            signed_file = self.request(
                path="/sign",
                method="POST",
                files=files

            )
            return signed_file
        except Exception as e:
            logger.error(e)
            return None
    
    def sign_string(self, content:str):
        """
        sign the content string with the private key linked to the confidential environment
        """
        try:
            #convert the string into binary
            file_like_object = io.BytesIO(content.encode('utf-8'))
            files={'file': ('file.txt', file_like_object)}
            return self.sign(files)
        except Exception as e:
            logger.error(e)
            return None
    
    def sign_json(self, collaboration_space_id:str,json_payload:dict):
        """
        create signed json (json web signature https://datatracker.ietf.org/doc/html/rfc7515) based on json payload 
        """
        try:
            #convert the string into binary
            file_like_object = io.BytesIO(json.dumps(json_payload).encode('utf-8'))
            files={'file': ('file.txt', file_like_object)}
            signature=self.sign(files)
            protected={}
            protected["alg"]="RS256"
            protected["x5u"]=self.client.get_public_key_url(collaboration_space_id)
            jws={}
            jws["payload"]=self.base64_encode_string(json.dumps(json_payload))
            jws["protected"]=self.base64_encode_string(json.dumps(protected))
            jws["signature"]=signature
            return jws
        except Exception as e:
            logger.error(e)
            return None
    
    def base64_encode_string(self, content:str):
        content_bytes = content.encode('ascii')
        base64_bytes = base64.b64encode(content_bytes)
        return base64_bytes.decode('ascii')

    def request(
        self,
        path: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        content_type: str = None,
        data: dict | str | None = None,
        files: str | None = None,
    ) -> str | bytes | dict | list:
        """wrapper of python requests to interact with the secret-manager API

        Args:
            path (str): api endpoint
            method (Literal[GET, POST, PUT, DELETE], optional): http method. Defaults to "GET".
            content_type (str, optional): requested content type. Defaults to None.
            data (dict, optional): data argument. Defaults to None.
            files: (file): file argument. Defaults to None.

        Returns:
            _type_: _description_
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"[HTTP {method}] {url}")

        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        response = requests.request(method, url, headers=headers, data=data, files=files)
        response.raise_for_status()

        if response.headers["content-type"] and "application/json" in response.headers["content-type"]:
            return response.json()
        else:
            return response.text