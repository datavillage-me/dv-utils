"""
CLI interface for dv_utils.
"""
import logging

from . import DefaultListener, default_settings, process_event_dummy

logger = logging.getLogger(__name__)
logger.info("executing default")

# let the log go to stdout, as it will be captured by the cage operator
logging.basicConfig(
    level=default_settings.log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

DefaultListener(process_event_dummy, daemon=default_settings.daemon)
