import requests
import json
import base64
from os import environ
from dv_utils import audit_log, LogLevel

"""
Fetches a resource from a pod using acp protocol and return as string
"""
def get_acp_from_pod_url(pod_url: str, path: str, solid_oidp_token: str = None, verify_grant: bool = False) -> str:
  resource_uri = f"{pod_url}/{path}"

  if not solid_oidp_token:
    solid_oidp_token = __get_dv_soidp_token()

  uma_token = get_uma_token(solid_oidp_token, resource_uri, verify_grant)

  res = requests.get(resource_uri, headers={'Authorization': f"Bearer {uma_token}"})
  if not res.ok:
    audit_log(f"Could not get file with uma token. Got [{res.status_code}]: {res.text}")
    return None
  
  return res.text

def __get_dv_soidp_token() -> str:
  token_endpoint = f"https://solid-idp.datavillage.me/token"  # TODO: how to configure solid idp?
  webid = __get_cage_webid()
  appid = __get_cage_appid()
  user_name = environ['SOLID_IDP_USERNAME']
  password = environ['SOLID_IDP_PASSWORD']

  query_params = {'webid': webid, 'appid': appid}

  res = requests.get(token_endpoint, params=query_params, auth=(user_name, password))
  if not res.ok:
    audit_log(f"Could not get token from solid idp. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)

  return res.json()['token']

def __get_cage_webid() -> str:
  api_url = environ['DV_URL']
  space_id = environ['DV_APP_ID']
  return f"{api_url}/.well-known/{space_id}/webid"

def __get_cage_appid() -> str:
  api_url = environ['DV_URL']
  space_id = environ['DV_APP_ID']
  return f"{api_url}/.well-known/{space_id}/appid" 

"""
Fetches a UMA token that can be used to fetch a resource from an ACP POD
"""
def get_uma_token(solid_idp_token: str, resource_uri: str, access_grant: dict | None = None, verify_grant: bool = False):
  # Call 1: get premission ticket from uma
  (uma_uri, permission_ticket) = get_permission_ticket(resource_uri)

  # Call 2: get uma configuration
  uma_configuration = get_uma_configuration(uma_uri)
  uma_token_endpoint = uma_configuration['token_endpoint']

  vc_configuration = get_vc_configuration(uma_configuration['verifiable_credential_issuer'])

  # If no access grant given: find needed access grant
  if access_grant is None:
    access_grant = find_access_grant(solid_idp_token, resource_uri, vc_configuration['derivationService'], verify_grant)

  elif verify_grant and not verify_verifiable_credential(access_grant, vc_configuration['verifierService']):
    audit_log(f"access grant not valid {access_grant['id']}", LogLevel.ERROR)
    return None

  # Call 3: get uma token without scopes
  uma_unscoped_token = __request_uma_unscoped_token(access_grant, uma_token_endpoint, permission_ticket) 

  # Call 4: get uma token with scopes
  return __request_uma_scoped_token(uma_token_endpoint, permission_ticket, solid_idp_token, uma_unscoped_token)

"""
Fetches permission ticket by doing an unauthenticated fetch
returns (uma_uri, permission ticket)
"""
def get_permission_ticket(resource_uri: str) -> tuple[str, str]:
  res = requests.get(resource_uri)

  if res.status_code != 401:
    audit_log(f"Expected status code 401, got {res.status_code}", LogLevel.ERROR)
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

"""
Fetches all access requests for a Solid OIDP token from the vc and finds the first one applicable to the given resource
"""
def find_access_grant(solid_idp_token: str, resource_uri: str, vc_derive_endpoint: str, verify_grants: bool = False) -> dict:
  filtered_access_grants = [r for r in get_all_access_grants(vc_derive_endpoint, solid_idp_token) if __is_access_grant_for_resource(resource_uri, r, verify_grants)]
  if not len(filtered_access_grants):
    audit_log(f"Could not find access request for resource {resource_uri}", LogLevel.ERROR)
    return None
  
  return filtered_access_grants[0]

"""
Fetches all access requests for a given Solid OIDP token
"""
def get_all_access_grants(vc_derive_endpoint: str, solid_id_token: str, verify_grant: bool = False) -> list[dict]:
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

  if verify_grant:
    verifiable_credentials: list = res_json['verifiableCredential']
    return [vc for vc in verifiable_credentials if verify_verifiable_credential(vc)]

  return res_json['verifiableCredential']

def __is_access_grant_for_resource(resource_uri: str, access_grant: dict, verify_grant: bool = False) -> bool:
  if verify_grant:
    vc_server = access_grant['issuer']
    vc_configuration = get_vc_configuration(vc_server)
    vc_verify_endpoint = vc_configuration['verifierService']
    return verify_verifiable_credential(access_grant, vc_verify_endpoint)

  # TODO: make edge case better
  provided_consent = access_grant['credentialSubject'].get('providedConsent', {'forPersonalData': ''})
  resource_in_request = provided_consent['forPersonalData']
  inherit = provided_consent.get('inherit', 'false') == 'true'

  # Grant can be used if the request gave access to the resource, or to a superfolder with inherit=true
  return resource_in_request == resource_uri or (inherit and resource_uri.startswith(resource_in_request))

def verify_verifiable_credential(verifiable_credential: dict, vc_verify_endpoint: str = None) -> bool:
  if not vc_verify_endpoint:
    vc_configuration = get_vc_configuration(verifiable_credential['issuer'])
    vc_verify_endpoint = vc_configuration['verifierService']

  verify_body = {
    "verifiableCredential": verifiable_credential
  }

  verify_response = requests.post(vc_verify_endpoint, json=verify_body, headers={'Content-Type': 'application/json'})
  if not verify_response.ok:
    audit_log(f"could not verify verifiable credential. Got [{verify_response.status_code}]: {verify_response.text}", LogLevel.ERROR)
    return False

  response_json = verify_response.json()

  # TODO: for now the warnings are ignored
  errors: list = response_json['errors']
  return len(errors) == 0

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

"""
Fetches access request for specific resource. Will only result in an access request for this exact resource, not a parent resource with inherit=True
"""
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
    audit_log(f"Could not search grants at VC. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)
    return []
  
  return res.json()['verifiableCredential']