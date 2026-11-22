"""Structured logging — every run is traceable in data/app.log."""
from __future__ import annotations

import logging
from pathlib import Path

from .config import get, ensure_dirs


_CONFIGURED = False



def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)