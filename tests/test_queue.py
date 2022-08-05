"""
Unit test for the redis and listen modules.
Remark: to test the process module, you need to have a running redis instance and set it's address in the .env.test file.
"""

import unittest

from dv_utils import RedisQueue, default_settings, process_event_dummy

default_settings.load_settings(".env.test")


class Test(unittest.TestCase):
    """
    Collection of test related to the redis queue
    """

    def setUp(self):
        self.test_event = {
            "userIds": [default_settings.config("TEST_USER")],
            "trigger": "full",
            # 'jobId': None,
        }

        self.redis_queue = RedisQueue()
        self.redis_queue.create_consummer_group()

    def tearDown(self):
        self.redis_queue.destroy_consummer_group()

    def test_process_queue_once(self):
        """
        Try the process by sending an event to the queue and consume exactly one event.
        """

        # fake the publishing of an event
        self.redis_queue.publish(self.test_event)

        # wait for exactly one event and process it
        event = self.redis_queue.listen_once()
        process_event_dummy(event)

    def test_process_queue_loop(self):
        """
        Try the process by sending an event to the queue and let the queue loop in wait.
        """

        # fake the publishing of an event
        self.redis_queue.publish(self.test_event)

        # let the queue wait for events and dispatch them to the process function
        self.redis_queue.listen(process_event_dummy, 2)
