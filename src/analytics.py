"""Monthly summaries, trends, comparisons, running balance."""
from __future__ import annotations

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    g = df.groupby("month")["amount"]
    out = pd.DataFrame({
        "spent": g.apply(lambda s: s[s < 0].abs().sum()),
        "earned": g.apply(lambda s: s[s > 0].sum()),
        "count": g.count(),
    }).fillna(0).reset_index()
    out["net"] = out["earned"] - out["spent"]
    out["cumulative_net"] = out["net"].cumsum()
    out["mom_change_pct"] = out["spent"].pct_change().mul(100).round(1)
    return out



def spend_by_category(df: pd.DataFrame) -> pd.DataFrame:
    spend = df[df["amount"] < 0].copy()
    out = (
        spend.groupby("category")["amount"].sum().abs()
        .reset_index(name="amount").sort_values("amount", ascending=False)
    )
    total = out["amount"].sum() or 1
    out["pct"] = (out["amount"] / total * 100).round(1)
    return out



def monthly_by_category(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["amount"] < 0].copy()
    d["month"] = d["date"].dt.to_period("M").astype(str)
    return (
        d.groupby(["month", "category"])["amount"].sum().abs()
        .unstack(fill_value=0)
    )

