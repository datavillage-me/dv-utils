"""
This module define a redis event listener with prioritition functionality.
"""

from typing import Any, Callable

from ..process import process_event_dummy
from ..redis import RedisQueue
from ..log_utils import audit_log
import time

class PriorityListener:
    """
    listener for message on the the redis queue while passing a priority list
    """

    def __init__(
        self, event_processor: Callable[[dict], Any] = process_event_dummy, daemon=False, log_events=True, stream_priorities = ["events"]
    ):
        # Instantiate the local Datavillage Redis queue
        self.redis_queue = RedisQueue()
        self.redis_queue.create_consummer_group(stream_priorities)
        self.event_processor = event_processor
        self.stream_priorities = stream_priorities

        self.__listen(daemon, log_events)

    def __listen(self, daemon, log_events):
        if(daemon):
           audit_log(log="Algo Event Listener started", app="algo")

        while True:
          evt = self.__listen_once()
          if evt:
            self.__handle_event(evt, log_events)
          if not daemon:
          #stop after one event
            break

        if(daemon):
           audit_log(log="Algo Event Listener Ended", app="algo")

    def __listen_once(self):
      for stream_name in self.stream_priorities:
        evt = self.redis_queue.listen_once(stream_name=stream_name, timeout=1)
        if evt:
          return evt
      
      return None
    
    def __handle_event(self, evt, log_events):
      start = time.time()
      evt_type =evt.get("type", "MISSING_TYPE")
      if(log_events):
        audit_log("Event processing started", evt=evt_type, state="STARTED", app="algo")

      try:
        self.event_processor(evt)
      except Exception as err:
        if(log_events):
          audit_log("Event processing failed", evt=evt_type, state="FAILED", app="algo", error=str(err), processing_time=time.time()-start)
      else:
        if(log_events):
          audit_log("Event processing done", evt=evt_type, state="DONE", app="algo", processing_time=time.time()-start)
      

