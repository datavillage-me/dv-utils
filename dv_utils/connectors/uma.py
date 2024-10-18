import copy
import os

from dv_utils.connectors.connector import Configuration
from dv_utils import audit_log, solid_utils

SOLID_IDP_USERNAME = os.environ.get('SOLID_IDP_USERNAME')
SOLID_IDP_PASSWORD = os.environ.get('SOLID_IDP_PASSWORD')
WEB_ID = "https://pbibbopb.webid.sndk-dev.datavillage.me"

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
    solid_id_token = solid_utils.get_token(WEB_ID, f"{WEB_ID}/appid", SOLID_IDP_USERNAME, SOLID_IDP_PASSWORD)
    print(f"got token {solid_id_token}")
    # TODO: refactor to have the UMA flow in separate method for clarity
    # Call 1
    (uma_uri, permission_ticket) = solid_utils.get_permission_ticket(pod_url, self.config.path)
    
    # Call 2
    uma_config = solid_utils.get_uma_configuration(uma_uri)
    vc_server = uma_config['verifiable_credential_issuer']
    token_endpoint = uma_config['token_endpoint']

    access_grants = solid_utils.get_all_access_grants(vc_server, solid_id_token)

    # Call 3
     
    return ""
  



