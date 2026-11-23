"""Multi-method anomaly detection: z-score, IQR, MAD, Isolation Forest."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import get
from .logger import get_logger

_log = get_logger(__name__)


def _by_category(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Broadcast a per-category statistic back onto every row."""
    stats = df.groupby("category")[col].transform("mean")
    return stats


def _zscore(df: pd.DataFrame, z: float) -> pd.DataFrame:
    df = df.copy()
    mean = df.groupby("category")["amount"].transform("mean")
    std = df.groupby("category")["amount"].transform("std").replace(0, np.nan)
    df["z"] = (df["amount"] - mean) / std
    df["flag_z"] = df["z"].abs() > z
    return df



def _iqr(df: pd.DataFrame, k: float) -> pd.DataFrame:
    df = df.copy()
    q1 = df.groupby("category")["amount"].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby("category")["amount"].transform(lambda s: s.quantile(0.75))
    iqr = (q3 - q1).replace(0, np.nan)
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    df["flag_iqr"] = (df["amount"] < lower) | (df["amount"] > upper)
    return df
