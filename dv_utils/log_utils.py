"""
This module defines utility functions for interaction with the loki server
"""
import time
import os
import httpx
import sys
from enum import Enum

class LogLevel(Enum):
    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40

def prepare_log(app_id:str|None, log:str|None=None, data:dict|None=None, app="operator", **extra_labels):
    if(log is None and data is None):
        return None, None
    if(app_id is None):
        app_id = os.environ.get("DV_CAGE_ID",None)
    if(app_id is None):
        return None, None

    if(data is None):
        data={}
    if("message" in data):
        log = data.pop("message")
    if("log" in data):
        log = data.pop("log")


    app_hash = app_id.rsplit("-")[-1]
    app_namespace = f"app-{app_hash}"
    app = "algo"
    data = {"streams": [{ "stream": { "namespace":app_namespace, "app": app, "audit":"true", **data, **extra_labels }, "values": [ [ str(time.time_ns()), log ] ] }]}
    return app_namespace, data

def get_loki_url() -> str:
    return os.environ.get("DV_LOKI", "http://loki.datavillage.svc.cluster.local:3100")

# Set default value of app back to 'algo'
def audit_log(log:str|None=None, data:dict|None=None, app_id:str|None=None, app="michiel-local", level:LogLevel = LogLevel.INFO, **extra_labels):
    log_dict = {'level': level.name}
    log_dict.update({'log': log} if type(log) == str else log)

    log_json = {"streams": [{ "stream": { "app": f"{app}" }, "values": [ [ str(time.time_ns()), str(log_dict) ] ] }]}
    app_namespace, _ = prepare_log(app_id, '', None)

    loki_url = get_loki_url()
    if loki_url.upper() == 'STDOUT':
        print(log)
    elif loki_url.upper() == 'STDERR':
        print(log, file=sys.stderr)
    elif(app_namespace):
        __push_loki(loki_url, log_json, app_namespace)
    else:
        # code shouldn't get here
        pass
       

def __push_loki(url: str, data: dict, app_namespace: str):
    r = httpx.post(url=f'{url}/loki/api/v1/push', json=data, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
    if(r.status_code!=204):
        print(f"Error pushing log {r}", flush=True) 

async def audit_log_async(log:str|None=None, data:dict|None=None, app_id:str|None=None, app="algo", **extra_labels):
    app_namespace, data = prepare_log(app_id=app_id, log=log, data=data, app=app, **extra_labels)
    if(app_namespace):
       async with httpx.AsyncClient() as client:
           r = await client.post(url=f'{get_loki_url()}/loki/api/v1/push', json=data, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
           if(r.status_code!=204):
               print(f"Error pushing log {r}", flush=True)
