"""
Unit test for the process module.
"""

import unittest

from dv_utils import default_settings, process_event_dummy

default_settings.load_settings(".env.test")


class Test(unittest.TestCase):
    """
    collection of test related to event processing

    """

    def test_process(self):
        """
        Try the process on a single user configured in the test .env file, without going through the redis queue
        """
        test_event = {
            "userIds": [default_settings.config("TEST_USER")],
            "trigger": "full",
            # 'jobId': None,
        }

        process_event_dummy(test_event)
