"""Detect likely recurring transactions (subscriptions, rent, utilities)."""
from __future__ import annotations

import pandas as pd


def detect_recurring(df: pd.DataFrame, min_occurrences: int = 3) -> pd.DataFrame:
    d = df[df["amount"] < 0].copy()
    d["day_of_month"] = d["date"].dt.day
    d["month"] = d["date"].dt.to_period("M")

    rows = []
    for merchant, g in d.groupby("merchant"):
        if len(g) < min_occurrences:
            continue
        month_counts = g.groupby("month").size()
        if month_counts.max() > 2:      # more than twice in a month — not recurring
            continue
        day_std = g["day_of_month"].std()
        amount_cv = g["amount"].std() / abs(g["amount"].mean()) if len(g) > 1 else 0
        if day_std <= 4 and amount_cv < 0.25:
            rows.append({
                "merchant": merchant,
                "occurrences": len(g),
                "avg_amount": round(abs(g["amount"].mean()), 2),
                "avg_day": int(g["day_of_month"].mean()),
                "category": g["category"].mode().iloc[0],
            })
    return pd.DataFrame(rows).sort_values("avg_amount", ascending=False)