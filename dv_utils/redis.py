"""
This module define the RedisQueue handling class
"""
import datetime
import json
from .log_utils import log, LogLevel

import redis
import os

from .settings import settings as default_settings



class RedisQueue:
    """
    Client to the local redis queue exposed in the cage.
    """

    def __init__(
        self,
        host=default_settings.redis_host,
        port=default_settings.redis_port,
        consumer_name=None,
    ):
        self.consumer_group = "consumers"
        if consumer_name:
            self.consumer_name = consumer_name
        else:
            cage_id = os.environ.get("DV_CAGE_ID")
            self.consumer_name = f"cage-{cage_id}"

        self.redis = redis.Redis(host, port, db=0)
        

    def create_consumer_group(self, stream_names = ["events"]) -> None:
        """
        Create the consumer group if it does not exist
        """
        for s in stream_names:
            try:
                self.redis.xgroup_create(s, self.consumer_group, mkstream=True)
            except redis.exceptions.ResponseError as error:
                if str(error).startswith("BUSYGROUP"):
                    pass
                else:
                    log(f"could not create consumer group {s}: {str(error)}", LogLevel.ERROR)

    def destroy_consumer_group(self) -> None:
        """
        Remove the consumer group if it exists
        """
        self.redis.xgroup_destroy("events", self.consumer_group)

    def publish(self, data: dict, create_consumer_group=False, stream_name="events") -> str:
        """
        publish an event to the redis queue

        Args:
            data (dict): event data to publish
            create_consumer_group (bool, optional): create the consumer group if it does not exist. Defaults to True.
            stream_name (str, default=events): the stream_name to publish the events to

        Returns:
            str: message id
        """

        if create_consumer_group:
            self.create_consumer_group()

        msg_id = self.redis.xadd(
            stream_name,
            {
                "msg_data": json.dumps(
                    data | {"msg_dt": datetime.datetime.utcnow().isoformat()}
                ),
            },
            maxlen=1000,
            approximate=True,
        )
        return msg_id

    def listen_once(self, timeout=120, stream_name = "events", debug_log = True):
        """
        Listen to the redis queue until one message is obtained, or timeout is reached
        :param timeout: timeout delay in seconds
        :param stream_name: name of the stream to listen to
        :return: the received message, or None
        """
        if debug_log:
            log("Waiting for message...", LogLevel.DEBUG)
        messages = self.redis.xreadgroup(
            self.consumer_group,
            self.consumer_name,
            {stream_name: ">"},
            noack=True,
            count=1,
            block=timeout * 1000,
        )
        if messages:
            message = [
                json.loads(msg_data.get(b"msg_data", "{}"))
                | {"msg_id": msg_id.decode()}
                for msg_id, msg_data in messages[0][1]
            ][0]
            if debug_log:
                msg_id = message["msg_id"]
                log(f"Received message {msg_id}...", LogLevel.DEBUG)
            return message
        return None
