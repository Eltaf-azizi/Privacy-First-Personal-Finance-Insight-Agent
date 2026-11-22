"""Three forecasting strategies: mean, linear, Holt-Winters."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .analytics import monthly_summary
from .config import get
from .logger import get_logger

_log = get_logger(__name__)


def _mean_forecast(series: pd.Series) -> float:
    return float(series.tail(3).mean())


def _linear_forecast(series: pd.Series) -> float:
    if len(series) < 2:
        return float(series.mean())
    x = np.arange(len(series))
    coef = np.polyfit(x, series.values, 1)
    return float(np.polyval(coef, len(series)))


def _hw_forecast(series: pd.Series) -> float:
    try:
        from statsmodels.tsa.holtwinters import SimpleExpSmoothing
        fit = SimpleExpSmoothing(series.values).fit()
        return float(fit.forecast(1)[0])
    except Exception:
        return _linear_forecast(series)


def forecast_next_month(df: pd.DataFrame, method: str = None) -> dict:
    method = method or get("forecast", "method", "linear")
    ms = monthly_summary(df)
    if ms.empty:
        return {"value": None, "method": method}

    series = ms["spent"].tail(get("forecast", "window_months", 6))
    fn = {"mean": _mean_forecast,
          "linear": _linear_forecast,
          "holtwinters": _hw_forecast}.get(method, _linear_forecast)
    value = fn(series)
    _log.info("Forecast next month via %s: %.2f", method, value)
    return {"value": round(value, 2), "method": method,
            "history": series.tolist()}
