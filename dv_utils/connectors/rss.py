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
    headers = {}
    download = False
    download_directory = None
    file_name = None

class RssConnector():
  config: RssConfiguration

  def __init__(self, config: RssConfiguration) -> None:
    self.config = copy.copy(config)

  def get(self):
    resp = requests.get(self.config.url, headers=self.config.headers)

    if(resp.status_code > 399):
      raise Exception(f"Fetching RSS feeds returned status [{resp.status_code}]: {resp}")

    if (self.config.download):
      path = os.path.join(self.config.download_directory, self.config.file_name)
      with open(path, 'w') as file:
        file.write(resp.text)
    else:
      rss = feedparser.parse(resp.text)
      if(rss.bozo):
        raise rss.bozo_exception
      return rss
