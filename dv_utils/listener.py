"""
This module define a default redis event listener processor as an example.
"""

from typing import Any, Callable

from .process import process_event_dummy
from .redis import RedisQueue
from .log_utils import audit_log
import time

class DefaultListener:
    """
    default listener for message on the the redis queue
    """

    def __init__(
        self, event_processor: Callable[[dict], Any] = process_event_dummy, daemon=False, log_events=True,
    ):
        # Instantiate the local Datavillage Redis queue
        redis_queue = RedisQueue()
        redis_queue.create_consummer_group()

        if(daemon):
           audit_log(log="Algo Event Listener started", app="algo")

        while True:
           evt = redis_queue.listen_once()
           if evt:
               start = time.time()
               evt_type =evt.get("type", "MISSING_TYPE")
               if(log_events):
                  audit_log("Event processing started", evt=evt_type, state="STARTED", app="algo")

               try:
                  event_processor(evt)
               except Exception as err:
                  if(log_events):
                     audit_log("Event processing failed", evt=evt_type, state="FAILED", app="algo", error=str(err), processing_time=time.time()-start)
               else:
                  if(log_events):
                     audit_log("Event processing done", evt=evt_type, state="DONE", app="algo", processing_time=time.time()-start)
               
          
           if not daemon:
               #stop after one event
               break

        if(daemon):
           audit_log(log="Algo Event Listener Ended", app="algo")

