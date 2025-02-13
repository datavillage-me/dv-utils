"""
CLI interface for dv_utils.
"""
from . import DefaultListener, default_settings, process_event_dummy



DefaultListener(process_event_dummy, daemon=default_settings.daemon)
