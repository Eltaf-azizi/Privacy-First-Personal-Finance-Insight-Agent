"""Per-category budget tracking."""
from __future__ import annotations

import pandas as pd

from .analytics import monthly_by_category


def category_budgets(df: pd.DataFrame, budgets: dict[str, float]) -> pd.DataFrame:
    mc = monthly_by_category(df)
    if mc.empty:
        return pd.DataFrame()

    latest = mc.iloc[-1]
    rows = []
    for cat, budget in budgets.items():
        actual = float(latest.get(cat, 0.0))
        rows.append({
            "category": cat,
            "budget": budget,
            "actual": actual,
            "remaining": round(budget - actual, 2),
            "over_budget": actual > budget,
            "progress_pct": round(min(actual / budget * 100, 100), 1) if budget else 0,
        })
    return pd.DataFrame(rows).sort_values("progress_pct", ascending=False)