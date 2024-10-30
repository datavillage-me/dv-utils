import requests
import json
import base64
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
  res_json = res.json()
  print(f"got response from vc {res.status_code}: {res_json}")
  return res_json

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

def get_uma_token(solid_idp_token: str, resource_uri: str, access_grant: dict):
  # Call 1: get premission ticket from uma
  (uma_uri, permission_ticket) = get_permission_ticket(resource_uri)

  # Call 2: get uma configuration
  uma_configuration = get_uma_configuration(uma_uri)
  uma_token_endpoint = uma_configuration['token_endpoint']

  # Call 3: get uma token without scopes
  uma_unscoped_token = __request_uma_unscoped_token(access_grant, uma_token_endpoint, permission_ticket) 

  # Call 4: get uma token with scopes
  return __request_uma_scoped_token(uma_token_endpoint, permission_ticket, solid_idp_token, uma_unscoped_token)

# Following docs
# def __request_uma_unscoped_token(solid_idp_token: str, uma_token_endpoint:str, permission_ticket: str) -> str:
#   payload = {
#     'ticket': permission_ticket,
#     'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
#     'claim_token': solid_idp_token,
#     'claim_token_format': 'http://openid.net/specs/openid-connect-core-1_0.html#IDToken'
#   }

#   headers = {
#     'Content-Type': 'application/x-www-form-urlencoded'
#   }

#   res = requests.post(uma_token_endpoint, payload, headers=headers)
  
#   if not res.ok:
#     audit_log(f"Could not get unscoped uma token. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)
#     return ""
  
#   res_json = res.json()
#   with open('first_response.json', 'w') as f:
#     json.dump(res_json, f)
#   return res_json['access_token']

# As suggested by Athumi
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

  with open('athumi_suggestion_first_request.json', 'w') as f:
    json.dump(payload, f)

  res = requests.post(uma_token_endpoint, payload, headers=headers)
  
  if not res.ok:
    audit_log(f"Could not get unscoped uma token. Got [{res.status_code}]: {res.text}", LogLevel.ERROR)
    return ""
  
  res_json = res.json()
  with open('athumi_suggestion_first_response.json', 'w') as f:
    json.dump(res_json, f)
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

  with open('athumi_suggestion_second_request.json', 'w') as f:
    json.dump(payload, f)

  if not res.ok:
    audit_log(f"Could not get scoped uma token. Got [{res.status_code}]: {res.text}")
    return ""
  
  res_json = res.json()
  with open('athumi_suggestion_second_response.json', 'w') as f:
    json.dump(res_json, f)
  return res_json['access_token']

# Following docs
# def __request_uma_scoped_token(uma_token_endpoint: str, permission_ticket: str, access_grant: dict, unscoped_token: str) -> str:
#   verifiable_presentation = {
#     '@context': ['https://www.w3.org/2018/credentials/v1'],
#     'type': 'VerifiablePresentation',
#     'verifiableCredential': [access_grant]
#   }

#   with open('vp.json', 'w') as f:
#     json.dump(verifiable_presentation, f)

#   vp_bytes = json.dumps(verifiable_presentation).encode()
#   vp_b64 = base64.b64encode(vp_bytes).decode()
  
#   payload = {
#     'ticket': permission_ticket,
#     'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
#     'claim_token': vp_b64,
#     'claim_token_format': "https://www.w3.org/TR/vc-data-model/#json-ld",
#     'rpt': unscoped_token
#   }

#   headers = {
#     'Content-Type': 'application/x-www-form-urlencoded'
#   }

#   res = requests.post(uma_token_endpoint, payload, headers=headers)

#   if not res.ok:
#     audit_log(f"Could not get scoped uma token. Got [{res.status_code}]: {res.text}")
#     return ""
  
#   res_json = res.json()
#   with open('second_response.json', 'w') as f:
#     json.dump(res_json, f)
#   return res_json['access_token']