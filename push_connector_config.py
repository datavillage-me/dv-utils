import os
import json


def push_config():
  # API_URL = os.environ['DV_API_URL']
  # DV_TOKEN = os.environ['DV_TOKEN']
  
  connector_dir = os.path.join('dv_utils', 'connectors')

  for file in os.listdir(connector_dir):
    if file.endswith('.json'):
      with open(os.path.join(connector_dir, file), 'r') as f:
        schema = json.loads(f.read())['schema']
        print(schema)


  

if __name__ == '__main__':
  push_config()