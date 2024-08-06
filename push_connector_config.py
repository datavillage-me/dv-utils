import os
import json
import requests

def load_configs() -> list[dict]:
  connector_dir = os.path.join('dv_utils', 'connectors')
  configs = []

  for file in os.listdir(connector_dir):
    if file.endswith('.json'):
      with open(os.path.join(connector_dir, file), 'r') as f:
        config = json.loads(f.read())
        name = file[:-len('.json')]
        config['name'] = name.capitalize()

        configs.append(config)

  return configs

def push_configs():
  API_URL = os.environ['DV_URL']
  DV_TOKEN = os.environ['DV_TOKEN']
  schemas = load_configs()
  headers = {'Authorization': f'Bearer {DV_TOKEN}'}
  endpoint = f'{API_URL}/connectors'

  for conn_config in schemas:
    res = requests.put(endpoint, headers=headers, json=conn_config)
    if (res.status_code < 200 or res.status_code > 299):
      print(f'Something went wrong when pushing configuration {res.text}')

  print('done')
  exit(0)


if __name__ == '__main__':
  push_configs()