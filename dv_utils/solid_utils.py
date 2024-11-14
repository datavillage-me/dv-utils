import requests
import json
import base64
from os import environ
from dv_utils import audit_log, LogLevel

# TODO: encapsulate methods + clean up the file

def get_acp_from_pod_url(pod_url: str, path: str) -> str:
  resource_uri = f"{pod_url}/{path}"

  # Get cage solid token
  cage_webid = get_cage_webid()
  cage_appid = get_cage_appid()
  cage_token = get_dv_soidp_token(cage_webid, cage_appid)
  print(cage_token)

  # Get UMA token
  uma_token = get_uma_token(cage_token, resource_uri)

  # Get file
  res = requests.get(resource_uri, headers={'Authorization': f"Bearer {uma_token}"})
  if not res.ok:
    audit_log(f"Could not get file with uma token. Got [{res.status_code}]: {res.text}")
    return None
  
  return res.text

def get_cage_webid() -> str:
  api_url = environ['DV_URL']
  space_id = environ['DV_APP_ID']
  return f"{api_url}/.well-known/{space_id}/webid"

def get_cage_appid() -> str:
  api_url = environ['DV_URL']
  space_id = environ['DV_APP_ID']
  # TODO: figure out how we handle our appids
  return f"{api_url}/.well-known/{space_id}/appid" 

def get_dv_soidp_token(webId: str, appId: str) -> str:
  token_endpoint = f"https://solid-idp.datavillage.me/token"  # TODO: how to configure solid idp?
  user_name = environ['SOLID_IDP_USERNAME']
  password = environ['SOLID_IDP_PASSWORD']

  query_params = {'webid': webId, 'appid': appId}

  res = requests.get(token_endpoint, params=query_params, auth=(user_name, password))
  if not res.ok:
    audit_log(f"Could not get token from solid idp. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)

  return res.json()['token']

"""
Fetches permission ticket to access a resource through UMA flow
returns (uma_uri, permission ticket)
"""
def get_permission_ticket(resource_uri: str) -> tuple[str, str]:
  res = requests.get(resource_uri)

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

def get_all_access_grants(vc_derive_endpoint: str, solid_id_token: str) -> list[dict]:
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
  if not res.ok:
    audit_log(f"Could not get all access grants. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)
    return None

  res_json = res.json()

  return res_json['verifiableCredential']

def get_access_grant_for_resource(vc_derive_endpoint: str, solid_id_token: str, resource_uri: str) -> list[dict]:
  body = {
    'verifiableCredential': {
      'credentialSubject': {
      'providedConsent': {
        'forPersonalData': resource_uri
      }
    }
    }
  }

  headers = {
    'Authorization': f"Bearer {solid_id_token}",
    'Content-Type': 'application/json'
  }

  res = requests.post(vc_derive_endpoint, json=body, headers=headers)

  if not res.ok:
    audit_log(f"Could not search grants at VC. Got [{res.status_code}]: {res.text}")
    return []
  
  return res.json()['verifiableCredential']

"""
Fetches a UMA token that can be used to fetch a resource from an ACP POD
"""
def get_uma_token(solid_idp_token: str, resource_uri: str, access_request: dict | None = None):
  # Call 1: get premission ticket from uma
  (uma_uri, permission_ticket) = get_permission_ticket(resource_uri)

  # Call 2: get uma configuration
  uma_configuration = get_uma_configuration(uma_uri)
  uma_token_endpoint = uma_configuration['token_endpoint']

  # If no access grant given: find needed access grant
  if access_request is None:
    vc_configuration = get_vc_configuration(uma_configuration['verifiable_credential_issuer'])
    access_request = find_access_request(solid_idp_token, resource_uri, vc_configuration['derivationService'])

  # Call 3: get uma token without scopes
  uma_unscoped_token = __request_uma_unscoped_token(access_request, uma_token_endpoint, permission_ticket) 

  # Call 4: get uma token with scopes
  return __request_uma_scoped_token(uma_token_endpoint, permission_ticket, solid_idp_token, uma_unscoped_token)

def find_access_request(solid_idp_token: str, resource_uri: str,  vc_derive_endpoint: str) -> dict:
  filtered_access_requests = [r for r in get_all_access_grants(vc_derive_endpoint, solid_idp_token) if __is_access_request_for_resource(resource_uri, r)]
  if not len(filtered_access_requests):
    audit_log(f"Could not find access request for resource {resource_uri}", LogLevel.ERROR)
    return None
  
  return filtered_access_requests[0]

def __is_access_request_for_resource(resource_uri: str, access_request: dict) -> bool:

  # TODO: make edge case better
  provided_consent = access_request['credentialSubject'].get('providedConsent', {'forPersonalData': ''})
  resource_in_request = provided_consent['forPersonalData']
  inherit = provided_consent.get('inherit', 'false') == 'true'

  # Grant can be used if the request gave access to the resource, or to a superfolder with inherit=true
  return resource_in_request == resource_uri or (inherit and resource_uri.startswith(resource_in_request))



def __request_uma_unscoped_token(access_grant_body: dict, uma_token_endpoint:str, permission_ticket: str) -> str:
  verifiable_presentation = {
    '@context': ["https://www.w3.org/2018/credentials/v1"],
    'type': ["VerifiablePresentation"],
    'verifiableCredential': [access_grant_body]
  }
  vp_bytes = json.dumps(verifiable_presentation).encode()
  vp_b64 = base64.b64encode(vp_bytes).decode()

  payload = {
    'ticket': permission_ticket,
    'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
    'claim_token': vp_b64,
    'claim_token_format': 'https://www.w3.org/TR/vc-data-model/#json-ld'
  }

  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  res = requests.post(uma_token_endpoint, payload, headers=headers)
  
  if not res.ok:
    audit_log(f"Could not get unscoped uma token. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)
    return ""
  
  res_json = res.json()

  return res_json['access_token']

# As suggested by Athumi
def __request_uma_scoped_token(uma_token_endpoint: str, permission_ticket: str, solid_idp_token: str, unscoped_token: str) -> str:
  payload = {
    'ticket': permission_ticket,
    'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
    'claim_token': solid_idp_token,
    'claim_token_format': "http://openid.net/specs/openid-connect-core-1_0.html#IDToken",
    'rpt': unscoped_token
  }

  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  res = requests.post(uma_token_endpoint, payload, headers=headers)

  if not res.ok:
    audit_log(f"Could not get scoped uma token. Got [{res.status_code}]: {res.text}")
    return ""
  
  res_json = res.json()

  return res_json['access_token']

