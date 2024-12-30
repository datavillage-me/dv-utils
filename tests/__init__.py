"""
collection of tests for the project
"""
import logging

from . import test_process, test_queue,test_contract,test_secret_manager

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
