"""
Multi-tier categorisation:
  Tier 1 — deterministic keyword rules (highest confidence)
  Tier 2 — previously-learned corrections (from user feedback)
  Tier 3 — local LLM (Ollama, only for unmatched)
  Tier 4 — ML classifier (Naive Bayes trained on labelled sample)
  Fallback — "Other"

No data leaves the machine. Only Tier 3 makes any network call, and it
is hard-restricted to localhost via src.privacy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import get
from .logger import get_logger
from .privacy import assert_local, audit

_log = get_logger(__name__)

RULES: dict[str, list[str]] = {
    "Groceries": ["WALMART", "TESCO", "ALDI", "LIDL", "SAINSBURY", "MORRISONS", "COSTCO", "WHOLE FOODS"],
    "Transport": ["UBER", "LYFT", "SHELL", "BP", "TFL", "OYSTER", "TRAINLINE", "NATIONAL RAIL", "EXXON"],
    "Dining":    ["STARBUCKS", "MCDONALD", "PRET", "DELIVEROO", "JUST EAT", "CAFE", "RESTAURANT", "NANDO"],
    "Utilities": ["BRITISH GAS", "THAMES WATER", "OCTOPUS", "EDF", "E.ON", "SCOTTISH POWER", "TV LICENCE"],
    "Shopping":  ["AMAZON", "ARGOS", "EBAY", "ASOS", "ZARA", "H&M", "IKEA"],
    "Health":    ["BOOTS", "PHARMACY", "NHS", "DENTAL", "GYM", "PUREGYM"],
    "Entertainment": ["NETFLIX", "SPOTIFY", "DISNEY", "STEAM", "PLAYSTATION", "CINEMA", "VUE"],
}

CATEGORIES = sorted(list(RULES.keys()) + ["Income", "Other"])



# ---- Tier 1: rules ---------------------------------------------------------

def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["category"] = pd.NA
    df["confidence"] = 0.0
    text = df["merchant"].fillna("").astype(str)
    for cat, keywords in RULES.items():
        for kw in keywords:
            mask = text.str.contains(kw, na=False) & df["category"].isna()
            df.loc[mask, "category"] = cat
            df.loc[mask, "confidence"] = 1.0
    return df

