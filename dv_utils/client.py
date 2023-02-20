"""
This module define the client class to interact with the Data-village API.
"""

import logging
from typing import Literal

import rdflib
import requests

from .settings import Settings
from .settings import settings as default_settings

logger = logging.getLogger(__name__)


class Client:
    """
    Http client to interact with the Data-village API.
    """

    def __init__(self, settings: Settings = None):
        self.settings: Settings = settings or default_settings

    def get_users(self):
        """
        Returns the list of active users for this application
        """
        user_ids = self.request(
            f"/clients/{self.settings.client_id}/applications/{self.settings.app_id}/activeUsers"
        )

        return user_ids

    def get_data(self, user_id: str, rdf_format: str = "turtle"):
        """
        Returns the available data for a given user.
        If the format is turtle (default), the returned value is an rdflib graph.
        """
        raw_data = self.request(
            f"/clients/{self.settings.client_id}/applications/{self.settings.app_id}/activeUsers/{user_id}/data"
        )
        if rdf_format in ["turtle"]:
            assert isinstance(raw_data, str | bytes)
            rdf_data = rdflib.Graph()
            rdf_data.parse(data=raw_data, format=rdf_format)
            return rdf_data
        else:
            # Currently no other format than turtle is supported
            raise Exception(f"Unknown format {format}")

    def write_results(self, user_id: str, filename: str, content: str):
        """
        Writes the results into the pod.
        """

        # currently only 'inferences' and 'explains' are supported
        if not filename in ["inferences", "explains"]:
            raise Exception("Unsupported result file name: " + filename)

        self.request(
            f"/clients/{self.settings.client_id}/applications/{self.settings.app_id}/activeUsers/{user_id}/{filename}",
            method="PUT",
            data=content,
        )

    def request(
        self,
        path: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        content_type: str = None,
        data: dict | str | None = None,
    ) -> str | bytes | dict | list:
        """wrapper of python requests to interact with the Data-village API

        Args:
            path (str): api endpoint
            method (Literal[GET, POST, PUT, DELETE], optional): http method. Defaults to "GET".
            content_type (str, optional): requested content type. Defaults to None.
            data (dict, optional): data argument. Defaults to None.

        Returns:
            _type_: _description_
        """
        url = f"{self.settings.base_url}{path}"
        logger.debug(f"[HTTP {method}] {url}")

        headers = {"Authorization": f"Bearer {self.settings.token}"}
        if content_type:
            headers["Content-Type"] = content_type

        response = requests.request(method, url, headers=headers, data=data)
        response.raise_for_status()

        if response.headers["content-type"] and "application/json" in response.headers["content-type"]:
            return response.json()
        else:
            return response.text
