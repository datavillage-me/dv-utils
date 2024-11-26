import copy

from dv_utils import solid_utils
from dv_utils.connectors.connector import Configuration
from ..log_utils import audit_log, LogLevel

class SolidConfiguration(Configuration):
  schema_file = "solid.json"
  connect_type = "solid"

  description = None
  path = None
  pod_url = None
  verify_grants = False

class SolidConnector():
  config: SolidConfiguration

  def __init__(self, config: SolidConfiguration) -> None:
    self.config = copy.copy(config)

  def get(self) -> str:
    return solid_utils.get_acp_from_pod_url(self.config.pod_url, self.config.path, verify_grant=self.config.verify_grants)