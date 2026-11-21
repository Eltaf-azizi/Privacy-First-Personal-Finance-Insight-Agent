"""SQLite persistence — all local."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)

DB_PATH = Path("data/transactions.db")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

