"""
This module defines utility functions for interaction with the loki server
"""
import time
import os
import httpx

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
    app = "web"
    data = {"streams": [{ "stream": { "namespace":app_namespace, "app": app, "audit":"true", **data, **extra_labels }, "values": [ [ str(time.time_ns()), log ] ] }]}
    return app_namespace, data
     
def audit_log(log:str|None=None, data:dict|None=None, app_id:str|None=None, app="algo", **extra_labels):
    app_namespace, data = prepare_log(app_id=app_id, log=log, data=data, app=app, **extra_labels)
    if(app_namespace):
       r = httpx.post(url='http://loki.datavillage.svc.cluster.local:3100/loki/api/v1/push', json=data, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
       if(r.status_code!=204):
          print(f"Error pushing log {r}", flush=True)

async def audit_log_async(log:str|None=None, data:dict|None=None, app_id:str|None=None, app="algo", **extra_labels):
    app_namespace, data = prepare_log(app_id=app_id, log=log, data=data, app=app, **extra_labels)
    if(app_namespace):
       async with httpx.AsyncClient() as client:
           r = await client.post(url='http://loki.datavillage.svc.cluster.local:3100/loki/api/v1/push', json=data, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
           if(r.status_code!=204):
               print(f"Error pushing log {r}", flush=True)
