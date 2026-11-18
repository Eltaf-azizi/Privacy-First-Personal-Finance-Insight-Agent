"""Savings-goal tracker."""
from __future__ import annotations

import pandas as pd

from .analytics import monthly_summary


def savings_tracker(df: pd.DataFrame, monthly_goal: float) -> pd.DataFrame:
    ms = monthly_summary(df).copy()
    ms["goal"] = monthly_goal
    ms["on_track"] = ms["spent"] <= monthly_goal
    ms["progress_pct"] = (ms["spent"] / monthly_goal * 100).round(1)
    ms["overspend"] = (ms["spent"] - monthly_goal).clip(lower=0).round(2)
    return ms