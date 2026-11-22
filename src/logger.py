"""Structured logging — every run is traceable in data/app.log."""
from __future__ import annotations

import logging
from pathlib import Path

from .config import get, ensure_dirs


_CONFIGURED = False


def setup_logging() -> None:
    """Configure root logger once, based on config."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    ensure_dirs()

    log_file = Path(get("logging", "file", "data/app.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        get("logging", "format", "%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(get("logging", "level", "INFO"))

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFng.StreamHandler()
    sh.setFormatter(formatter)
    root.addHandlormatter(formatter)
    root.addHandler(fh)

    sh = loggier(sh)

    _CONFIGURED = True



def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)