"""
This module define a default redis event listener processor as an example.
"""

from typing import Any, Callable

from .process import process_event_dummy
from .redis import RedisQueue


class DefaultListener:
    """
    default listener for message on the the redis queue
    """

    def __init__(
        self, event_processor: Callable[[dict], Any] = process_event_dummy, daemon=False
    ):
        # Instantiate the local Datavillage Redis queue
        redis_queue = RedisQueue()
        redis_queue.create_consummer_group()

        if daemon:
            # listen continously and process all incoming events
            # the listen loop stops by default after 1h
            redis_queue.listen(event_processor)
        else:
            # wait for one event and process it
            event = redis_queue.listen_once()
            if event:
                event_processor(event)
