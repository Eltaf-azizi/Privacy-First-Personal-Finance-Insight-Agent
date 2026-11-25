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



# ---- Tier 2: learned corrections ------------------------------------------

CORRECTIONS_DB = Path("data/corrections.db")


def load_corrections() -> dict[str, str]:
    if not CORRECTIONS_DB.exists():
        return {}
    import sqlite3
    conn = sqlite3.connect(CORRECTIONS_DB)
    try:
        rows = conn.execute("SELECT merchant, category FROM corrections").fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {m: c for m, c in rows}


def save_correction(merchant: str, category: str) -> None:
    import sqlite3
    CORRECTIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CORRECTIONS_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS corrections (merchant TEXT PRIMARY KEY, category TEXT)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO corrections (merchant, category) VALUES (?, ?)",
        (merchant, category),
    )
    conn.commit()
    conn.close()
    _log.info("Saved correction: %s → %s", merchant, category)


def apply_corrections(df: pd.DataFrame) -> pd.DataFrame:
    corrections = load_corrections()
    if not corrections:
        return df
    mask = df["category"].isna() & df["merchant"].isin(corrections)
    df.loc[mask, "category"] = df.loc[mask, "merchant"].map(corrections)
    df.loc[mask, "confidence"] = 0.95
    return df



# ---- Tier 3: local LLM -----------------------------------------------------

def _ask_ollama(description: str) -> tuple[str, float]:
    import requests
    url = get("categorise", "llm_endpoint", "http://localhost:11434/api/generate")
    assert_local(url)  # raises if non-local
    model = get("categorise", "llm_model", "llama3.2")
    prompt = (
        f"Categorise into one of: {', '.join(CATEGORIES)}.\n"
        f"Transaction: '{description}'\nReply with category only."
    )
    try:
        r = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        out = r.json().get("response", "").strip().split()[0].strip(".,'\"")
        if out in CATEGORIES:
            audit("LLM_CATEGORISE", f"{description[:40]} -> {out}")
            return out, 0.75
    except Exception as e:
        _log.warning("LLM call failed: %s", e)
    return "Other", 0.1

