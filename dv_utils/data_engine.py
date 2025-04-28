import os
from dv_data_engine_client import Client
from .log_utils import log, LogLevel

def create_client() -> Client:
  data_engine_url = os.environ.get("DATA_ENGINE_URL", None)
  if not data_engine_url:
    log("no data engine url found", LogLevel.ERROR)
    return None
  return Client(base_url=data_engine_url)