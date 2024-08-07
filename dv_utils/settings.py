"""
This module define the settings for the DV-utils package.
"""

import os
from decouple import Config, RepositoryEnv


class Settings:
    """
    Settings for the application
    """

    def __init__(self):
        self.load_settings()

    def load_settings(self, dotenv_file: str = None):
        """load the settings from a file in argument, or in environment variable or default

        Args:
            dotenv_file (str, optional): path to a dotenv file. Defaults to None.
        """

        # get config from argument, environment variable or from .env file
        dotenv_file = dotenv_file or os.environ.get("DOTENV_FILE", None)
        if dotenv_file:
            config = Config(RepositoryEnv(dotenv_file))
        else:
            config = Config(".")

        self.config = config

        self.base_url: str = config("DV_URL", default="", cast=str)
        self.token: str = config("DV_TOKEN", default="", cast=str)
        self.collaboration_space_id: str = config("DV_APP_ID", default="", cast=str)
        self.collaboration_space_owner_id: str = config("DV_CLIENT_ID", default="", cast=str)

        self.log_level = config("LOGLEVEL", default="INFO", cast=str)
        self.daemon = config("DAEMON", default=False, cast=bool)

        self.redis_host = config("REDIS_SERVICE_HOST", default="localhost", cast=str)
        self.redis_port = config("REDIS_SERVICE_PORT", default="6379", cast=str)

        self.data_connector_config_location = config("DATA_CONNECTOR_CONFIG_LOCATION", default="/resources/data", cast=str)

        self.data_user_output_location = config("DATA_USER_OUTPUT_LOCATION", default="/resources/outputs", cast=str)


settings = Settings()
