import requests
from dv_utils import audit_log

"""
Fetches permission ticket to access a resource through UMA flow
returns (uma_uri, permission ticket)
"""
def get_permission_ticket(pod_url: str, path: str) -> tuple[str, str]:
  res = requests.get(f"{pod_url}{'' if pod_url.endswith('/') else '/'}{path}")

  if res.status_code != 401:
    audit_log(f"Expected status code 401, got {res.status_code}")
    return {}
  
  # UMA as_uri="https://uma...", ticket="ey...",...
  [uma_uri_part, ticket_part] = res.headers['www-authenticate'].split(',')[:2]

  uma_uri_start = uma_uri_part.index('"') + 1
  uma_uri = uma_uri_part[uma_uri_start:-1]

  ticket_start = ticket_part.index('"') + 1
  ticket = ticket_part[ticket_start:-1]

  return (uma_uri, ticket)

def get_uma_configuration(uma_uri: str) -> dict:
  res = requests.get(f"{uma_uri}{'' if uma_uri.endswith('/') else '/'}.well-known/uma2-configuration")
  return res.json()