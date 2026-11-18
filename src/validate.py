"""Schema and data validation before any analytics runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str]
    warnings: List[str]

    def summary(self) -> str:
        lines = [f"Valid: {self.ok}"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        return "\n".join(lines)


def validate_transactions(df: pd.DataFrame) -> ValidationReport:
    """Return a report describing data-quality issues."""
    errors: List[str] = []
    warnings: List[str] = []

    required = {"date", "description", "amount"}
    missing = required - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {sorted(missing)}")
        return ValidationReport(False, errors, warnings)

    if df.empty:
        errors.append("DataFrame is empty")

    n_before = len(df)
    n_after = len(df.dropna(subset=["date", "amount"]))
    if n_after < n_before:
        warnings.append(f"{n_before - n_after} rows dropped (NaT/NaN)")

    if (df["amount"] == 0).any():
        warnings.append(f"{(df['amount'] == 0).sum()} zero-amount rows")

    if df["date"].min() > df["date"].max():
        errors.append("date range inverted")

    future = (df["date"] > pd.Timestamp.utcnow().tz_localize(None)).sum()
    if future > 0:
        warnings.append(f"{future} future-dated rows")

    ok = len(errors) == 0
    if not ok:
        _log.error("Validation failed: %s", errors)
    else:
        _log.info("Validation OK (%d rows, %d warnings)", len(df), len(warnings))
    return ValidationReport(ok, errors, warnings)