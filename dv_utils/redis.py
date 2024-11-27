"""
This module define the RedisQueue handling class
"""
import datetime
import json
import logging

import redis
import os

from .settings import settings as default_settings

logger = logging.getLogger(__name__)


class RedisQueue:
    """
    Client to the local redis queue exposed in the cage.
    """

    def __init__(
        self,
        host=default_settings.redis_host,
        port=default_settings.redis_port,
        consumer_name="consummer-0",
    ):
        self.consumer_group = "consummers"
        self.consumer_name = consumer_name
        self.redis = redis.Redis(host, port, db=0, ssl=True, ssl_ca_certs=os.environ.get("TLS_CAFILE",None))

    def create_consummer_group(self, stream_names = ["events"]) -> None:
        """
        Create the consummer group if it does not exist
        """
        for s in stream_names:
            try:
                self.redis.xgroup_create(s, self.consumer_group, mkstream=True)
            except redis.exceptions.ResponseError as error:
                if str(error).startswith("BUSYGROUP"):
                    pass
                else:
                    raise error

    def destroy_consummer_group(self) -> None:
        """
        Remove the consummer group if it exists
        """
        self.redis.xgroup_destroy("events", self.consumer_group)

    def publish(self, data: dict, create_consumer_group=False, stream_name="events") -> str:
        """
        publish an event to the redis queue

        Args:
            data (dict): event data to publish
            create_consumer_group (bool, optional): create the consummer group if it does not exist. Defaults to True.
            stream_name (str, default=events): the stream_name to publish the events to

        Returns:
            str: message id
        """

        if create_consumer_group:
            self.create_consummer_group()

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

    def listen_once(self, timeout=120, stream_name = "events"):
        """
        Listen to the redis queue until one message is obtained, or timeout is reached
        :param timeout: timeout delay in seconds
        :param stream_name: name of the stream to listen to
        :return: the received message, or None
        """
        logging.debug("Waiting for message...")
        messages = self.redis.xreadgroup(
            "consummers",
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
            msg_id = message["msg_id"]
            logging.debug(f"Received message {msg_id}...")
            return message
        return None
