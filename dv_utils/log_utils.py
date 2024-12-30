"""
This module defines utility functions for interaction with the loki server
"""
import time
import datetime
import httpx
import sys
from enum import Enum
from importlib.metadata import version

from .settings import settings as default_settings

class LogLevel(Enum):
    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    AUDIT = 50

# Holds metadata about the current event that is added to every log statement
# Do not create an object of this class in code
class LogMetadata:
    def __init__(self):
        self.evt = None
        self.evt_received = None
        self.evt_stream = None
        self.app_id = default_settings.config("DV_APP_ID", None)
        self.lib_version = version('dv-utils')

    def set_event(self, evt: dict, evt_stream: str, evt_received_ns: int | None = None):
        self.evt = evt
        self.evt_stream = evt_stream
        self.evt_received = evt_received_ns if evt_received_ns is not None else time.time_ns()

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

_metadata = LogMetadata()

def get_loki_url() -> str:
    return default_settings.config("DV_LOKI", "http://loki.datavillage.svc.cluster.local:3100")

def get_app_namespace() -> str | None:
    cage_id = default_settings.config('DV_CAGE_ID', None)
    if not cage_id:
        return None
    else:
        return f'app-{cage_id}'

def set_event(evt: dict, stream: str = "events", evt_received_ns: int | None = None):
    _metadata.set_event(evt, stream, evt_received_ns)

def create_body(log: str, level: LogLevel, **kwargs):
    log_dict = dict()
    # First add kwargs so that the hardcoded keys don't get overwritten
    for k, v in kwargs.items():
        log_dict[k] = str(v)

    log_dict = {'msg': log}
    log_dict.update(dict(_metadata))
    log_dict.update({'level': level.name})
    log_dict.update({'timestamp': time.time_ns()})

    return log_dict

# TODO: should we also add an optional parameter `start_ns` to automatically add `duration_ns` (or whatever) field?
def audit_log(log:str, level:LogLevel = LogLevel.AUDIT, **kwargs):
    if log is None:
        return
    #add timestamp in the log
    data = create_body(log, level, **kwargs)
    now = datetime.datetime.now()
    formated_now = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    header=formated_now[:-3] + " - AUDIT - "
    print(header+str(data), file=sys.stderr)



# TODO: deprecate or delete
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
