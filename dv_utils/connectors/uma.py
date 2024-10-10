import copy

from dv_utils.connectors.connector import Configuration
from dv_utils import audit_log, solid_utils

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
    (uma_uri, permission_ticket) = solid_utils.get_permission_ticket(pod_url, self.config.path)
    print(uma_uri)
    print(permission_ticket)
    return ""
  



