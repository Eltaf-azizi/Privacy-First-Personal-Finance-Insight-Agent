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
