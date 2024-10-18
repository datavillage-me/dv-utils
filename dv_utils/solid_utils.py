import requests
from dv_utils import audit_log, LogLevel

def get_token(webId: str, appId: str, user_name: str, password: str) -> str:
  token_endpoint = f"https://solid-idp.datavillage.me/token"  # TODO: how to configure solid idp?
  query_params = {'webid': webId, 'appid': appId}
  print(f"uname {user_name}, password {password}")
  res = requests.get(token_endpoint, params=query_params, auth=(user_name, password))
  if not res.ok:
    audit_log(f"Could not get token from solid idp. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)

  return res.json()['token']

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
  res = requests.get(f"{uma_uri}/.well-known/uma2-configuration")
  return res.json()

def get_vc_configuration(vc_uri: str) -> dict:
  res = requests.get(f"{vc_uri}/.well-known/vc-configuration")
  return res.json()

def get_all_access_grants(vc_server: str, solid_id_token: str) -> list[dict]:
  vc_derive_endpoint = get_vc_configuration(vc_server)['derivationService']
  print(f"derive endpoint {vc_derive_endpoint}")
  body = {
    'verifiableCredential': {
      "@context": ['https://www.w3.org/2018/credentials/v1'],
      'credentialSubject': {}
    }
  }

  headers = {
    'Authorization': f"Bearer {solid_id_token}",
    'Content-Type': 'application/json'
  }

  res = requests.post(vc_derive_endpoint, json=body, headers=headers)
  res_json = res.json()
  print(f"got response from vc {res.status_code}: {res_json}")
  return res_json
