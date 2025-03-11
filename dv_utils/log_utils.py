"""
This module defines utility functions for interaction with the loki server
"""
import time
import json
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
        self.evt_type = None
        self.msg_id = None
        self.evt_received = None
        self.evt_stream = None
        self.cage_id = default_settings.config("DV_CAGE_ID", None)
        self.lib_version = version('dv-utils')

    def set_event(self, evt: dict, evt_stream: str, evt_received_ns: int | None = None):
        self.evt_type = evt.get("type", "UNKOWN_TYPE")
        self.msg_id = evt.get("msg_id", "UNKOWN_MSG_ID")
        self.evt_stream = evt_stream
        self.evt_received = evt_received_ns if evt_received_ns is not None else time.time_ns()

    def reset_event(self):
        self.evt = None
        self.evt_stream = None
        self.evt_received = None

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

_metadata = LogMetadata()

def get_app_namespace() -> str | None:
    cage_id = default_settings.config('DV_CAGE_ID', None)
    if not cage_id:
        return None
    else:
        return f'app-{cage_id}'

def set_event(evt: dict, stream: str = "events", evt_received_ns: int | None = None):
    _metadata.set_event(evt, stream, evt_received_ns)

def reset_event():
    _metadata.reset_event()

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

def log(log:str, level:LogLevel = LogLevel.INFO, **kwargs):
    if log is None:
        return
    #add timestamp in the log
    data = create_body(log, level, **kwargs)
    json_encoded = json.dumps(data)
    print(json_encoded, file=sys.stderr)
