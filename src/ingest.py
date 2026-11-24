"""
CSV ingestion with:
  • configurable column mapping
  • auto-detection of date/description/amount columns
  • multi-format date parsing
  • separate debit/credit handling
  • validation
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from .config import get
from .logger import get_logger
from .validate import validate_transactions
from .merchant import normalise

_log = get_logger(__name__)


# ---- Auto-detection helpers -------------------------------------------------

def _detect_date_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if pd.to_datetime(df[col], errors="coerce").notna().mean() > 0.8:
            return col
    return None



def _detect_amount_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if pd.to_numeric(df[col], errors="coerce").notna().mean() > 0.8:
            return col
    return None



def _detect_description_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if df[col].dtype == object and df[col].str.len().mean() > 4:
            return col
    return None

