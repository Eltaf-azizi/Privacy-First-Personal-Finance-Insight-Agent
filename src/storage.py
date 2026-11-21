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


def save_transactions(df: pd.DataFrame, table: str = "transactions") -> None:
    out = df.copy()
    if "date" in out.columns:
        out["date"] = out["date"].astype(str)
    conn = _conn()
    out.to_sql(table, conn, if_exists="replace", index=False)
    conn.close()
    _log.info("Saved %d rows to %s (%s)", len(out), DB_PATH, table)


def load_transactions(table: str = "transactions") -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = _conn()
    try:
        df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=["date"])
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df