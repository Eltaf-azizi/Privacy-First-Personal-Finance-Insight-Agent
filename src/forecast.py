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

