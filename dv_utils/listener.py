"""
This module define a default redis event listener processor as an example.
"""

from typing import Any, Callable

from .process import process_event_dummy
from .redis import RedisQueue
from .log_utils import log, set_event, LogLevel, reset_event
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
        try:
         redis_queue.create_consumer_group()
        except Exception as e:
           log(f"could not create consumer group: {str(e)}", LogLevel.ERROR)

        if(daemon):
           log(log="Algo Event Listener started", app="algo")

        while True:
           evt = None
           try:
            evt = redis_queue.listen_once()
           except Exception as e:
              log(f"could not listen to redis: {str(e)}")
              break
           
           if evt:
               start = time.time()
               evt_type =evt.get("type", "MISSING_TYPE")
               set_event(evt)
               if(log_events):
                  log("Event processing started", state="STARTED", app="algo")

               try:
                  event_processor(evt)
               except Exception as err:
                  if(log_events):
                     log("Event processing failed",  state="FAILED", app="algo", error=str(err), processing_time=time.time()-start)
               else:
                  if(log_events):
                     log("Event processing done", evt=evt_type, state="DONE", app="algo", processing_time=time.time()-start)
               
               reset_event() 
           if not daemon:
               #stop after one event
               break

        if(daemon):
           log(log="Algo Event Listener Ended", app="algo")

