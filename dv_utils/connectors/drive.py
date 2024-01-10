from dv_utils.connectors.connector import Configuration, is_valid_configuration
import io
import logging
import os
import copy
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


logger = logging.getLogger(__name__)

scope = ['https://www.googleapis.com/auth/drive.readonly']


class DriveConfiguration(Configuration):
    schema_file = "drive.json"
    project_id = None
    private_key_id = None
    private_key = None
    client_email = None
    client_id = None
    client_x509_cert_url = None
    resource_name = None
    file_name = None
    download_directory = None


class DriveConnector():
    config: DriveConfiguration

    service = None

    def __init__(self, config: DriveConfiguration) -> None:
        self.config = copy.copy(config)

        if not self.config.file_name:
            self.config.file_name = self.config.resource_name

        if not is_valid_configuration(self.config):
            logger.error('Configuration is not valid')

        json_config = {'private_key': self.config.private_key,
                       'client_email': self.config.client_email,
                       'private_key_id': self.config.private_key_id,
                       'client_id': self.config.client_id,
                       'type': 'service_account'}

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            json_config, scope)

        self.service = build('drive', 'v3', credentials=credentials)

    def get(self):

        results = self.service.files().list().execute()
        items = results.get('files', [])

        found = None
        if not items:
            logger.error("No files available on Google Drive")
            return
        else:
            for item in items:
                if (item['name'] == self.config.resource_name):
                    found = item

        if not found:
            logger.error(f"File <{self.config.resource_name}> not found")
            return

        request_file = self.service.files().get_media(fileId=found['id'])
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request_file)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        path = os.path.join(self.config.download_directory,
                            self.config.file_name)
        with open(path, 'wb') as f:
            f.write(file.getbuffer())
