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



def auto_detect_mapping(df: pd.DataFrame) -> dict:
    """Best-effort mapping for unfamiliar bank exports."""
    mapping: dict = {}
    d = _detect_date_column(df)
    a = _detect_amount_column(df)
    s = _detect_description_column(df)
    if d: mapping[d] = "date"
    if a: mapping[a] = "amount"
    if s: mapping[s] = "description"
    _log.info("Auto-detected mapping: %s", mapping)
    return mapping


# ---- Loader -----------------------------------------------------------------

def load_transactions(
    source: Union[str, Path, io.BytesIO],
    mapping: Optional[dict] = None,
    auto_map: bool = True,
) -> pd.DataFrame:
    """
    Load a bank CSV and return a canonical DataFrame
    with columns ['date', 'description', 'amount', 'merchant'].
    """
    raw = pd.read_csv(source)
    _log.info("Loaded raw CSV: shape=%s", raw.shape)

    if mapping is None:
        mapping = auto_detect_mapping(raw) if auto_map else {}

    
    # Debit/credit split handling
    debit_cfg = get("ingest", "amount_columns", {}).get("debit", [])
    credit_cfg = get("ingest", "amount_columns", {}).get("credit", [])
    debit_col = next((c for c in raw.columns if c in debit_cfg), None)
    credit_col = next((c for c in raw.columns if c in credit_cfg), None)

    if debit_col and credit_col:
        raw["__amount__"] = (
            pd.to_numeric(raw[credit_col], errors="coerce").fillna(0)
            - pd.to_numeric(raw[debit_col], errors="coerce").fillna(0)
        )
        mapping = {**mapping, "__amount__": "amount"}

    rename = {k: v for k, v in mapping.items() if k in raw.columns}
    df = raw.rename(columns=rename)
    df = df[[c for c in ("date", "description", "amount") if c in df.columns]]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "description" in df.columns:
        df["description"] = df["description"].astype(str)
        df["merchant"] = df["description"].map(normalise)
    else:
        df["description"] = ""
        df["merchant"] = ""

    df = df.dropna(subset=["date", "amount"]).reset_index(drop=True)

    report = validate_transactions(df)
    if not report.ok:
        raise ValueError(report.summary())

    _log.info("Ingested %d transactions (%s → %s)",
              len(df), df["date"].min().date(), df["date"].max().date())
    return df