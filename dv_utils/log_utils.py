"""
This module defines utility functions for interaction with the loki server
"""
import time
import httpx
import sys
from enum import Enum
from datetime import datetime

from .settings import settings as default_settings

class bcolors:
    DEFAULT = '\033[97m'
    TRACE = '\033[97m'
    DEBUG = '\033[97m'
    INFO = '\033[94m'
    WARN = '\033[93m'
    ERROR = '\033[91m'

class LogLevel(Enum):
    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40

def get_loki_url() -> str:
    return default_settings.config("DV_LOKI", "http://loki.datavillage.svc.cluster.local:3100")

def get_app_namespace() -> str | None:
    cage_id = default_settings.config('DV_CAGE_ID', None)
    if not cage_id:
        return None
    else:
        return f'app-{cage_id}'

def create_body(log: str | dict | None, level: LogLevel):
    log_dict = {'log': log} if type(log) == str else log 
    log_dict.update({'level': level.name})

    return {"streams": [{ "stream": { "app": "algo" }, "values": [ [ str(time.time_ns()), str(log_dict) ] ] }]} 

def audit_log(log:str|dict|None=None, level:LogLevel = LogLevel.INFO, **kwargs):
    loki_url = get_loki_url()
    if loki_url.upper() == 'STDOUT':
        time_string = datetime.now().strftime('%F %T,%f')[:-3]
        print(__get_color_for_log_level(level)+time_string+" - "+level.name+" - "+str(log))
        print(bcolors.DEFAULT)
    elif loki_url.upper() == 'STDERR':
        print(log, file=sys.stderr)
    else:
        data = create_body(log, level)
        __push_loki(loki_url, data)
       
def __get_color_for_log_level(level):
    if level==LogLevel.TRACE:
        return bcolors.TRACE
    elif level==LogLevel.DEBUG:
        return bcolors.DEBUG
    elif level==LogLevel.INFO:
        return bcolors.INFO
    elif level==LogLevel.WARN:
        return bcolors.WARN
    elif level==LogLevel.ERROR:
        return bcolors.ERROR
    else:
        return bcolors.DEFAULT
def __push_loki(url: str, data: dict):
    app_namespace = get_app_namespace()

    r = httpx.post(url=f'{url}/loki/api/v1/push', json=data, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
    if(r.status_code!=204):
        print(f"Error pushing log {r}", flush=True) 

async def audit_log_async(log:str|dict|None=None, level: LogLevel = LogLevel.INFO):
    loki_url = get_loki_url()
    if (loki_url == 'STDOUT' or loki_url == 'STDERR'):
        audit_log(log, level)
    else:
        app_namespace = get_app_namespace()
        body = create_body(log, level)
        async with httpx.AsyncClient() as client:
            r = await client.post(url=f'{get_loki_url()}/loki/api/v1/push', json=body, headers={"X-Scope-OrgID": app_namespace, "Content-Type": "application/json"})
            if(r.status_code!=204):
                print(f"Error pushing log {r}", flush=True)
