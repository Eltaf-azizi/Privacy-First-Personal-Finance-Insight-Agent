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



def category_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Per-category change between the last two months."""
    mc = monthly_by_category(df)
    if len(mc) < 2:
        return pd.DataFrame()
    last, prev = mc.iloc[-1], mc.iloc[-2]
    change = ((last - prev) / prev.replace(0, pd.NA) * 100).round(1)
    return pd.DataFrame({"last_month": last, "prev_month": prev,
                         "change_pct": change}).sort_values("change_pct")



def day_of_week_pattern(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["amount"] < 0].copy()
    d["dow"] = d["date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    out = (
        d.groupby("dow")["amount"].agg(["sum", "count"]).abs()
        .reindex(order, fill_value=0).reset_index()
    )
    out.columns = ["day", "amount", "count"]
    return out