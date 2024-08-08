"""
collection of tests for the project
"""
import logging

from . import test_process, test_queue,test_contract

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
