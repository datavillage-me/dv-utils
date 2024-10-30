from dv_utils.connectors import uma
from dv_utils import solid_utils
import json
import os
import requests

uname = os.environ.get('SOLID_IDP_USERNAME')
password = os.environ.get('SOLID_IDP_PASSWORD')
# token = solid_utils.get_token('https://pbibbopb.webid.sndk-dev.datavillage.me', 'https://pbibbopb.webid.sndk-dev.datavillage.me/appid', uname, password)
token = ""

file = "https://storage.sandbox-nl-pod.datanutsbedrijf.be/b6738617-737c-4a03-8178-b21543efe44b/sndk/userProfile.ttl"

# access_grants = solid_utils.get_access_grant_for_resource("https://vc.sandbox-nl-pod.datanutsbedrijf.be/derive", token, file)

grant_response = requests.get("https://vc.sandbox-nl-pod.datanutsbedrijf.be/vc/ed280108-6de1-484c-876d-2d3d15168611", headers={'Authorization': f"Bearer {token}"})
grant = grant_response.json()
with open('grant.json', 'w') as f:
  json.dump(grant, f)

# if not len(access_grants):
#   print("access grants is empty")
#   exit(0)

uma_access_token = solid_utils.get_uma_token(token, file, grant)
print(f"uma token {uma_access_token}")

headers = {
  'Authorization': f"Bearer {uma_access_token}"
}
profile = requests.get(file, headers=headers)
print(profile.status_code)
print(profile.text)

# config = uma.UmaConfiguration()
# config.path ='sndk/'

# conn = uma.UmaConnector(config)

# result = conn.get_from_pod('https://storage.sandbox-pod.datanutsbedrijf.be/d71c4922-35c5-4204-82f5-885c5af6c1c2/sndk/')
# print(result)