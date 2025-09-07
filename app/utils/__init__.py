"""
Utilities package for Document Intelligence Platform.

This package contains utility functions for:
- Text preprocessing and cleaning
- Confidence scoring
- Logging and monitoring
"""

from .preprocessing import clean_text
from .scoring import compute_confidence
from .logger import setup_logging, log_event

__all__ = [
    "clean_text",
    "compute_confidence", 
    "setup_logging",
    "log_event"
]