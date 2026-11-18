"""Schema and data validation before any analytics runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from .logger import get_logger

_log = get_logger(__name__)


@dataclass
class ValidationReport:
    ok: bool
    errors: List[str]
    warnings: List[str]

    def summary(self) -> str:
        lines = [f"Valid: {self.ok}"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        return "\n".join(lines)

