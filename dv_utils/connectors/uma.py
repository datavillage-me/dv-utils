import copy
import requests

from dv_utils.connectors.connector import Configuration
from dv_utils import audit_log

class UmaConfiguration(Configuration):
  schema_file = "uma.json"
  connect_type = "uma"

  path: str = None
  description: str = None

class UmaConnector():
  config: UmaConfiguration

  def __init__(self, config: UmaConfiguration) -> None:
    self.config = copy.copy(config)

  def get_from_pod(self, pod_url: str) -> str:
    (uma_uri, permission_ticket) = self.__get_ticket(pod_url, self.config.path)
    print(uma_uri)
    print(permission_ticket)
    return ""
  

  # TODO: create solid_utils file
  def __get_ticket(self, pod_url: str, path: str) -> tuple[str, str]:
    res = requests.get(f"{pod_url}/{path}")

    if res.status_code != 401:
      audit_log(f"Expected status code 401, got {res.status_code}")
      return {}
    
    # UMA as_uri="https://uma...", ticket="ey...",...
    [uma_uri_part, ticket_part] = res.headers['www-authenticate'].split(',')[:2]

    uma_uri_start = uma_uri_part.index('"') + 1
    uma_uri = uma_uri_part[uma_uri_start:-1]

    ticket_start = ticket_part.index('"') + 1
    ticket = ticket_part[ticket_start:-1]

    return(uma_uri, ticket)

