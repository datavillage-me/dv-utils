"""
This module contains util methods to retreive secrets for collaborators/clients
"""

import requests
import os
from .log_utils import log, LogLevel

def get_secret_for_collaborator(collaborator_id: str) -> str:
  secret_manager_key = f"collaborator-{collaborator_id}-server"
  return __get_secret(secret_manager_key)

def get_secret_for_client(client_id: str, secret_id: str) -> str:
  secret_manager_key = f"client-{client_id}-{secret_id}"
  return __get_secret(secret_manager_key)

def __get_secret(secret_id: str) -> str:
  secret_manager_url = os.environ.get("SECRET_MANAGER_URL", None)
  if secret_manager_url is None:
    log("secret manager url not found in environment", LogLevel.ERROR)
    return None

  resp = requests.get(f"{secret_manager_url}/secrets/{secret_id}")
  if resp.status_code != 200:
    log(f"could not get secret {secret_id}. Got [{resp.status_code}]: {resp.text}")
    return None
  
  return resp.text