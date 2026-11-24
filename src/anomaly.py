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


def _mad(df: pd.DataFrame, t: float) -> pd.DataFrame:
    """Modified z-score using median absolute deviation — robust to outliers."""
    df = df.copy()
    med = df.groupby("category")["amount"].transform("median")
    mad = (df["amount"] - med).abs().groupby(df["category"]).transform("median")
    mad = mad.replace(0, np.nan)
    df["mod_z"] = 0.6745 * (df["amount"] - med) / mad
    df["flag_mad"] = df["mod_z"].abs() > t
    return df


def _isoforest(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        df["flag_iso"] = False
        return df

    df["flag_iso"] = False
    for cat, group in df.groupby("category"):
        if len(group) < 10:
            continue
        model = IsolationForest(contamination=0.05, random_state=42)
        preds = model.fit_predict(group[["amount"]])
        df.loc[group.index, "flag_iso"] = preds == -1
    return df


def flag_anomalies(
    df: pd.DataFrame,
    methods: list[str] = None,
    z: float = None,
    iqr_k: float = None,
    mad_t: float = None,
) -> pd.DataFrame:
    if methods is None:
        methods = get("anomaly", "methods", ["zscore", "iqr", "mad"])
    if z is None:
        z = get("anomaly", "z_threshold", 2.5)
    if iqr_k is None:
        iqr_k = get("anomaly", "iqr_multiplier", 1.5)
    if mad_t is None:
        iqr_k = get("anomaly", "iqr_multiplier", 1.5)
        mad_t = get("anomaly", "mad_threshold", 3.5)

    if "zscore" in methods:
        df = _zscore(df, z)
    if "iqr" in methods:
        df = _iqr(df, iqr_k)
    if "mad" in methods:
        df = _mad(df, mad_t)
    if "isoforest" in methods:
        df = _isoforest(df)

    flags = [c for c in df.columns if c.startswith("flag_")]
    df["anomaly_votes"] = df[flags].sum(axis=1)
    df["is_anomaly"] = df["anomaly_votes"] >= max(2, len(flags) // 2 + 1)
    df["severity"] = df["anomaly_votes"].map(
        lambda v: "critical" if v >= 3 else ("warning" if v == 2 else "info")
    )

    _log.info("Anomaly detection: %d flagged (methods=%s)",
              int(df["is_anomaly"].sum()), methods)
    return df
    