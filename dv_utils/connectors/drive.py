from dv_utils.connectors.connector import Configuration, is_valid_configuration
import io
import logging
import os
import copy
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


logger = logging.getLogger(__name__)

scope = ['https://www.googleapis.com/auth/drive']


class DriveConfiguration(Configuration):
    schema_file = "drive.json"

    private_key_id = None
    private_key = None
    client_email = None
    client_id = None

    resource_name = None
    resource_id = None
    resource_directory_id = None
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

        found = None

        if not self.config.resource_id:
            results = self.service.files().list().execute()
            items = results.get('files', [])
            if not items:
                logger.error("No files available on Google Drive")
                return
            else:
                def is_item(item):
                    if self.config.resource_id:
                        return item['id'] == self.config.resource_id
                    return item['name'] == self.config.resource_name
                for item in items:
                    if is_item(item):
                        found = item

            if not found:
                logger.error(f"File <{self.config.resource_name}> not found")
                return
        else:
            found = {'id': self.config.resource_id}

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

    def push(self, file_path):

        if not self.config.resource_directory_id:
            logger.error("No resource directory configured")
            return

        file_metadata = {"name": self.config.resource_name,
                         "parents": [self.config.resource_directory_id]}
        media = MediaFileUpload(file_path)

        self.service.files().create(body=file_metadata,
                                    media_body=media, fields="id").execute()
