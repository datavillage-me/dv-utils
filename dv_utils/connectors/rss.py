from dv_utils.connectors.connector import Configuration
import copy
import feedparser
import logging
import requests
import os

logger = logging.getLogger(__name__)

class RssConfiguration(Configuration):
    schema_file = "rss.json"
    url = None
    download_directory = None
    file_name = None

class RssConnector():
  config: RssConfiguration

  def __init__(self, config: RssConfiguration) -> None:
    self.config = copy.copy(config)

  def get(self):
    headers = {
      "Cache-Control": "max-age=0",
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    resp = requests.get(self.config.url, headers=headers)

    if(resp.status_code > 399):
      raise Exception(f"Fetching RSS feeds returned status [{resp.status_code}]")

    path = os.path.join(self.config.download_directory, self.config.file_name)
    with open(path, 'w') as file:
      file.write(resp.text)
